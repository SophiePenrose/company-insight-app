import streamlit as st
import json
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Company Fit Scoring Dashboard", layout="wide")

st.title("Company Fit Scoring Dashboard")

# Load results from latest baseline file
def get_latest_baseline_file():
    output_dir = Path("output")
    files = list(output_dir.glob("baseline_*.json"))
    if not files:
        return None
    return max(files, key=lambda f: f.stat().st_mtime)

def load_results():
    baseline_file = get_latest_baseline_file()
    if not baseline_file:
        st.warning("No baseline results found in output/.")
        return None, None
    with open(baseline_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("results", []), data.get("metadata", {})

results, metadata = load_results()
if not results:
    st.stop()

# Table view: core info
def make_table_data(results):
    rows = []
    for r in results:
        scoring = r.get("scoring") or {}
        rows.append({
            "Company Name": r.get("company_name"),
            "Company Number": r.get("company_number"),
            "Score": r.get("score"),
            "Tier": r.get("tier"),
            "Rank": r.get("rank"),
            "Prohibited": scoring.get("prohibited", False),
            "Last Analyzed": r.get("analyzed_at"),
        })
    return rows

table_data = make_table_data(results)
df = None
try:
    import pandas as pd
    df = pd.DataFrame(table_data)
except ImportError:
    df = table_data

st.subheader("Company Scores and Tiers")
if df is not None:
    st.dataframe(df, use_container_width=True)
else:
    st.write(table_data)

# Drill-down: select a company
def get_company_by_number(results, company_number):
    for r in results:
        if r.get("company_number") == company_number:
            return r
    return None

company_numbers = [r.get("company_number") for r in results]
selected_number = st.selectbox("Select a company to view details", company_numbers)
selected = get_company_by_number(results, selected_number)

if selected:
    st.markdown(f"## {selected.get('company_name')} ({selected.get('company_number')})")
    st.write(f"**Score:** {selected.get('score')}  |  **Tier:** {selected.get('tier')}  |  **Rank:** {selected.get('rank')}")
    st.write(f"**Last analyzed:** {selected.get('analyzed_at')}")
    scoring = selected.get("scoring") or {}
    if scoring.get("prohibited"):
        st.error(f"Prohibited: {scoring.get('prohibited_reason', 'See details')}")
    # Filing and extraction info
    st.subheader("Filing & Extraction Info")
    filings = selected.get("documents")
    if filings and isinstance(filings, list) and len(filings) > 0:
        for doc in filings:
            desc = doc.get("filing", {}).get("description", "[No description]")
            date = doc.get("filing", {}).get("date", "[No date]")
            downloaded = doc.get("downloaded")
            error = doc.get("error")
            st.write(f"- **{desc}** ({date}) | Downloaded: {downloaded}")
            if error:
                st.warning(f"  Extraction error: {error}")
    else:
        st.info("No filings or extraction attempts recorded for this company.")
    # Evidence breakdown
    st.subheader("Score Breakdown & Evidence")
    if scoring and isinstance(scoring, dict) and len(scoring) > 0:
        st.json(scoring)
    else:
        st.info("No scoring or evidence available for this company.")
    # Insights & messaging
    report = selected.get("report")
    if report and isinstance(report, dict) and len(report) > 0:
        st.subheader("Insights & Messaging")
        st.json(report)
    else:
        st.info("No insights or messaging available for this company.")
    # Extraction errors (pipeline-level)
    if selected.get("extraction_error"):
        st.warning(f"Extraction error: {selected['extraction_error']}")
    # Profile
    st.subheader("Company Profile")
    profile = selected.get("profile")
    if profile and isinstance(profile, dict) and len(profile) > 0:
        st.json(profile)
    else:
        st.info("No company profile available.")
    # Raw extraction
    extraction = selected.get("extraction")
    if extraction and isinstance(extraction, dict) and len(extraction) > 0:
        st.subheader("Raw Extraction")
        st.json(extraction)
    else:
        st.info("No extraction data available for this company.")
