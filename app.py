from src.services.gemini_fit import get_gemini_fit_score
import os
import json
import sys
from pathlib import Path
import time
import yaml
from src.clients.key_manager import APIKeyManager

import time
from dotenv import load_dotenv
import pandas as pd
import streamlit as st

# Load environment variables
load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.clients.companies_house import CompaniesHouseClient
from src.clients.ixbrl_converter import IXBRLConverterClient
from src.services.ch_document_ingest import collect_company_documents
from src.fit_scorer.pipeline import run_company_extraction

st.set_page_config(page_title="Revolut Business Prospect Readiness Engine", layout="wide")
st.markdown("""
<style>
.main .block-container { padding-top: 2rem; }
.metric-card { background: #f6f8fa; border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 1px 4px rgba(0,0,0,0.03); }
.company-table { margin-top: 1rem; }
</style>
""", unsafe_allow_html=True)

OUTPUT_DIR = Path("output")
CONFIG_PATH = Path("config/app_config.yaml")
with open(CONFIG_PATH, "r") as f:
    app_config = yaml.safe_load(f)

api_keys = app_config.get("companies_house_api_keys", [])
if not api_keys:
    st.error("No Companies House API keys found in config/app_config.yaml")
    st.stop()
batch_size = app_config.get("batch_size", 100)
max_docs = app_config.get("max_docs", 2)
fields_to_extract = app_config.get("fields_to_extract", [])

key_manager = APIKeyManager(api_keys)
OUTPUT_DIR.mkdir(exist_ok=True)
COMPANIES_FILE = OUTPUT_DIR / "companies_data.jsonl"
REPORTS_FILE = OUTPUT_DIR / "prospect_reports.jsonl"

def load_jsonl(path: Path):
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def append_jsonl(path: Path, row: dict):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")

def load_companies_from_csv(csv_path: str):
    df = pd.read_csv(csv_path, dtype={"company_number": str})
    # Ensure company_number is always a zero-padded 8-character string
    if "company_number" in df.columns:
        df["company_number"] = df["company_number"].apply(lambda x: str(x).zfill(8) if pd.notnull(x) else "")
    return df.to_dict('records')

def is_group_accounts_filing(description: str) -> bool:
    keywords = ["group accounts", "annual report and accounts", "full accounts", "accounts with group"]
    return any(keyword.lower() in description.lower() for keyword in keywords)

def get_latest_group_accounts(ch_client, company_number: str):
    try:
        history = ch_client.filing_history(company_number, items_per_page=100)
        items = history.get("items", [])
        for item in items:
            if is_group_accounts_filing(item.get("description", "")):
                return item
    except:
        pass
    return None

def calculate_fit_score(company_data: dict) -> int:
    # AI-powered fit score (Gemini/LLM)
    try:
        score = get_gemini_fit_score(company_data)
        return score
    except Exception as e:
        # Fallback to rule-based if Gemini fails
        turnover = company_data.get("turnover", 0)
        if turnover > 10000000:
            return 80
        elif turnover > 5000000:
            return 60
        else:
            return 40

st.title("Revolut Business Prospect Readiness Engine")
st.caption("Automated prospecting of UK mid-market companies for Revolut Business use cases.")

# Define tabs for UI
tab1, tab2 = st.tabs(["Company List & Upload", "Analysis Results"])

# Load API keys from env
ixbrl_key = os.getenv("IXBRL_API_KEY")
llm_key = os.getenv("LLM_KEY")

def get_ch_client():
    key = key_manager.get_key()
    return CompaniesHouseClient(key)

ixbrl_client = IXBRLConverterClient(ixbrl_key) if ixbrl_key else None

if llm_key is None:
    st.warning("LLM API key not found. Schema extraction will be disabled until LLM_KEY is set in your .env file.")

# Load companies from CSV
st.sidebar.header("Company list")
uploaded_file = st.sidebar.file_uploader("Upload company list CSV", type=["csv"])

companies = []
if uploaded_file is not None:
    try:
        companies = load_companies_from_csv(uploaded_file)
    except Exception as e:
        st.error(f"Could not load uploaded CSV: {e}")
        st.stop()
elif Path("company_numbers.csv").exists():
    try:
        companies = load_companies_from_csv("company_numbers.csv")
    except Exception as e:
        st.error(f"Could not load company_numbers.csv: {e}")
        st.stop()
else:
    st.error("No company list found. Upload a CSV file or add company_numbers.csv to the repo.")
    st.stop()

if not companies:
    st.error("Loaded company list is empty. Make sure the CSV has company_name and company_number columns.")
    st.stop()

with tab1:
    st.subheader("Company Analysis")
    st.write(f"Loaded {len(companies)} companies from CSV")
    for company in companies[:10]:  # Show first 10
        st.write(f"- {company.get('company_name', '')} ({company.get('company_number', '')})")
    if len(companies) > 10:
        st.write(f"... and {len(companies) - 10} more")

    if 'analysis_in_progress' not in st.session_state:
        st.session_state.analysis_in_progress = False
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = []
    if st.button("Analyze All Companies") and not st.session_state.analysis_in_progress:
        st.session_state.analysis_in_progress = True
        st.session_state.analysis_results = []
        st.session_state.analysis_index = 0
    if st.session_state.analysis_in_progress:
        progress = st.progress(0)
        status = st.empty()
        ch_client = get_ch_client()
        results_container = st.container()
        # Load progress from file if exists
        progress_file = OUTPUT_DIR / "analysis_progress.json"
        if progress_file.exists():
            with progress_file.open("r", encoding="utf-8") as f:
                progress_data = json.load(f)
                st.session_state.analysis_index = progress_data.get("index", 0)
                st.session_state.analysis_results = progress_data.get("results", [])
        for i in range(st.session_state.analysis_index, len(companies)):
            company = companies[i]
            company_number = company.get("company_number")
            company_name = company.get("company_name")
            status.write(f"Analyzing {i+1}/{len(companies)}: {company_name}")
            try:
                profile = ch_client.company_profile(company_number)
                filing = get_latest_group_accounts(ch_client, company_number)
                extraction_result = run_company_extraction(
                    ch_client=ch_client,
                    company_number=company_number,
                    company_name=company_name,
                    company_profile=profile,
                    max_docs=max_docs,
                    model="gpt-4o-mini" if llm_key else None,
                )
                if extraction_result is None:
                    company_data = {
                        "company_number": company_number,
                        "company_name": company_name,
                        "error": "Extraction pipeline returned None."
                    }
                else:
                    company_data = {
                        "company_number": company_number,
                        "company_name": company_name,
                        "profile": profile,
                        "latest_filing": filing,
                        "documents": extraction_result.get("documents"),
                        "extraction": extraction_result.get("extraction"),
                        "scoring": extraction_result.get("scoring"),
                        "extraction_error": extraction_result.get("extraction_error"),
                        "report": extraction_result.get("report"),
                    }
                    if ixbrl_client and filing:
                        financials = ixbrl_client.get_financials_metadata(company_number)
                        if financials:
                            company_data["financials"] = financials
                            company_data["turnover"] = financials.get("turnover", 0)
                    company_data["fit_score"] = calculate_fit_score(company_data)
                st.session_state.analysis_results.append(company_data)
            except Exception as e:
                company_data = {
                    "company_number": company_number,
                    "company_name": company_name,
                    "error": str(e)
                }
                st.session_state.analysis_results.append(company_data)
            st.session_state.analysis_index = i + 1
            # Save progress to file
            with progress_file.open("w", encoding="utf-8") as f:
                json.dump({"index": st.session_state.analysis_index, "results": st.session_state.analysis_results}, f)
            with COMPANIES_FILE.open("w", encoding="utf-8") as f:
                for r in st.session_state.analysis_results:
                    f.write(json.dumps(r) + "\n")
            with results_container:
                valid_results = [r for r in st.session_state.analysis_results if "error" not in r]
                if valid_results:
                    valid_results.sort(key=lambda x: (x.get("scoring") or {}).get("score", x.get("fit_score", 0)), reverse=True)
                    st.subheader("Prospect Candidates (partial)")
                    for company in valid_results[:10]:
                        with st.expander(f"{company['company_name']} - Score: {company.get('fit_score', 0)}/100"):
                            st.write(f"**Company Number:** {company['company_number']}")
                            st.write(f"**Turnover:** £{company.get('turnover', 'N/A')}")
                            if company.get('latest_filing'):
                                st.write(f"**Latest Filing:** {company['latest_filing'].get('description', 'N/A')}")
                            if company.get('documents'):
                                st.write("**Document status:**")
                                for doc in company['documents']:
                                    status_str = "✅ downloaded" if doc.get('downloaded') else "❌ failed"
                                    source = doc.get('text_source', 'n/a')
                                    st.write(f"- {doc.get('description', 'unknown')}: {status_str} ({source})")
                                    if doc.get('ocr_used'):
                                        st.write("  - OCR fallback used")
                                    if doc.get('error'):
                                        st.write(f"  - error: {doc.get('error')}")
                                    if doc.get('extracted_text'):
                                        snippet = doc['extracted_text'][:400].replace('\n', ' ')
                                        st.write(f"  - snippet: {snippet}...")
                            if company.get('extraction_error'):
                                st.error(f"Extraction error: {company.get('extraction_error')}")
                            if company.get('scoring'):
                                st.write("**Deterministic fit score:**")
                                scoring = company.get('scoring', {})
                                st.write(f"- Score: {scoring.get('score')}/100")
                                st.write(f"- Priority tier: {scoring.get('priority_tier')}")
                                st.write(f"- Confidence: {scoring.get('confidence')}")
                                st.write(f"- Summary: {scoring.get('summary')}")
                                breakdown = scoring.get('breakdown', {})
                                if breakdown:
                                    st.write("**Score breakdown:**")
                                    for key, value in breakdown.items():
                                        st.write(f"  - {key}: {value:.1f}")
                                explanations = scoring.get('explanations', [])
                                if explanations:
                                    st.write("**Explanation details:**")
                                    for item in explanations:
                                        st.write(f"- {item['component']}: {item['explanation']}")
                            if company.get('extraction'):
                                st.write("**LLM extraction summary:**")
                                extraction = company.get('extraction', {})
                                st.write(f"- Company name: {extraction.get('company_name', {}).get('value')}")
                                st.write(f"- Turnover: {extraction.get('turnover_gbp', {}).get('value')}")
                                st.write(f"- Industry: {extraction.get('industry', {}).get('value')}")
                                st.write(f"- Business model: {extraction.get('business_model', {}).get('value')}")
                                st.write(f"- Triggers: {extraction.get('triggers', {}).get('value')}")
                                st.write(f"- Providers detected: {len(extraction.get('providers', []))}")
                            if company.get('report'):
                                st.write("**Structured prospect report:**")
                                report = company.get('report', {})
                                st.write(f"- Report ID: {report.get('report_id')}")
                                st.write(f"- Generated at: {report.get('generated_at')}")
                                st.write(f"- Report status: {report.get('status')}")
                                st.write(f"- Document count: {len(report.get('documents', []))}")
                                if report.get('summary'):
                                    st.write(f"- Fit score: {report['summary'].get('fit_score')}")
                                    st.write(f"- Priority tier: {report['summary'].get('priority_tier')}")
                                    st.write(f"- Confidence: {report['summary'].get('confidence')}")
                                if report.get('company_summary'):
                                    st.write("**Company summary:**")
                                    for bullet in report['company_summary']:
                                        st.write(f"- {bullet}")
                                if report.get('pain_points'):
                                    st.write("**Identified gaps & pain points:**")
                                    for category, points in report['pain_points'].items():
                                        st.write(f"**{category.replace('_', ' ').title()}:**")
                                        for point in points:
                                            st.write(f"  - {point}")
                                if report.get('revolut_opportunity'):
                                    opp = report['revolut_opportunity']
                                    st.write("**Revolut Business opportunity:**")
                                    st.write(f"- {opp.get('pitch_summary')}")
                                    for uc in opp.get('recommended_use_cases', []):
                                        st.write(f"  - **{uc['product']}** ({uc['priority']}): {uc['fit']}")
                            ch_url = f"https://find-and-update.company-information.service.gov.uk/company/{company['company_number']}"
                            st.markdown(f"[View on Companies House]({ch_url})")
                            if company.get('report'):
                                st.write(f"Structured report written to `{REPORTS_FILE}`")
            progress.progress((i+1) / len(companies))
            # Instead of rerun, break to allow user to reload and resume
            st.info("Progress saved. You can reload the app to resume from here if needed.")
            break
        # If loop completes, mark as done and remove progress file
        if st.session_state.analysis_index >= len(companies):
            st.session_state.analysis_in_progress = False
            st.success("Analysis complete! Results saved.")
            if progress_file.exists():
                progress_file.unlink()


with tab2:
    # Analysis results and reports will be displayed here after running in tab1
    # (This section should not contain business logic or analysis code. It should only display results.)
    st.info("Run analysis to see results here.")

# Load and display results
if COMPANIES_FILE.exists():
    results = load_jsonl(COMPANIES_FILE)
    valid_results = [r for r in results if "error" not in r]
    
    if valid_results:
        # Sort by fit score descending
        valid_results.sort(
            key=lambda x: (x.get("scoring") or {}).get("score", x.get("fit_score", 0)), reverse=True
        )

        st.subheader("Prospect Candidates")

        for company in valid_results[:20]:  # Show top 20
            with st.expander(f"{company['company_name']} - Score: {company['fit_score']}/100"):
                st.write(f"**Company Number:** {company['company_number']}")
                st.write(f"**Turnover:** £{company.get('turnover', 'N/A')}")
                if company.get('latest_filing'):
                    st.write(f"**Latest Filing:** {company['latest_filing'].get('description', 'N/A')}")

                if company.get('documents'):
                    st.write("**Document status:**")
                    for doc in company['documents']:
                        status = "✅ downloaded" if doc.get('downloaded') else "❌ failed"
                        source = doc.get('text_source', 'n/a')
                        st.write(f"- {doc.get('description', 'unknown')}: {status} ({source})")
                        if doc.get('ocr_used'):
                            st.write("  - OCR fallback used")
                        if doc.get('error'):
                            st.write(f"  - error: {doc.get('error')}")
                        if doc.get('extracted_text'):
                            snippet = doc['extracted_text'][:400].replace('\n', ' ')
                            st.write(f"  - snippet: {snippet}...")

                if company.get('extraction_error'):
                    st.error(f"Extraction error: {company.get('extraction_error')}")

                if company.get('scoring'):
                    st.write("**Deterministic fit score:**")
                    scoring = company.get('scoring', {})
                    st.write(f"- Score: {scoring.get('score')}/100")
                    st.write(f"- Priority tier: {scoring.get('priority_tier')}")
                    st.write(f"- Confidence: {scoring.get('confidence')}")
                    st.write(f"- Summary: {scoring.get('summary')}")
                    breakdown = scoring.get('breakdown', {})
                    if breakdown:
                        st.write("**Score breakdown:**")
                        for key, value in breakdown.items():
                            st.write(f"  - {key}: {value:.1f}")
                    explanations = scoring.get('explanations', [])
                    if explanations:
                        st.write("**Explanation details:**")
                        for item in explanations:
                            st.write(f"- {item['component']}: {item['explanation']}")

                if company.get('extraction'):
                    st.write("**LLM extraction summary:**")
                    extraction = company.get('extraction', {})
                    st.write(f"- Company name: {extraction.get('company_name', {}).get('value')}")
                    st.write(f"- Turnover: {extraction.get('turnover_gbp', {}).get('value')}")
                    st.write(f"- Industry: {extraction.get('industry', {}).get('value')}")
                    st.write(f"- Business model: {extraction.get('business_model', {}).get('value')}")
                    st.write(f"- Triggers: {extraction.get('triggers', {}).get('value')}")
                    st.write(f"- Providers detected: {len(extraction.get('providers', []))}")

                if company.get('report'):
                    st.write("**Structured prospect report:**")
                    report = company.get('report', {})
                    st.write(f"- Report ID: {report.get('report_id')}")
                    st.write(f"- Generated at: {report.get('generated_at')}")
                    st.write(f"- Report status: {report.get('status')}")
                    st.write(f"- Document count: {len(report.get('documents', []))}")
                    if report.get('summary'):
                        st.write(f"- Fit score: {report['summary'].get('fit_score')}")
                        st.write(f"- Priority tier: {report['summary'].get('priority_tier')}")
                        st.write(f"- Confidence: {report['summary'].get('confidence')}")

                    if report.get('company_summary'):
                        st.write("**Company summary:**")
                        for bullet in report['company_summary']:
                            st.write(f"- {bullet}")

                    if report.get('pain_points'):
                        st.write("**Identified gaps & pain points:**")
                        for category, points in report['pain_points'].items():
                            st.write(f"**{category.replace('_', ' ').title()}:**")
                            for point in points:
                                st.write(f"  - {point}")

                    if report.get('revolut_opportunity'):
                        opp = report['revolut_opportunity']
                        st.write("**Revolut Business opportunity:**")
                        st.write(f"- {opp.get('pitch_summary')}")
                        for uc in opp.get('recommended_use_cases', []):
                            st.write(f"  - **{uc['product']}** ({uc['priority']}): {uc['fit']}")


                # Link to Companies House
                ch_url = f"https://find-and-update.company-information.service.gov.uk/company/{company['company_number']}"
                st.markdown(f"[View on Companies House]({ch_url})")

                if company.get('report'):
                    st.write(f"Structured report written to `{REPORTS_FILE}`")
    else:
        st.write("No valid results yet. Click 'Analyze All Companies' to start.")
else:
    st.write("No analysis data yet. Click 'Analyze All Companies' to start.")