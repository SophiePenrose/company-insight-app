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
            st.session_state.analysis_index = i + 1
                            if company.get('latest_filing'):
                            if company.get('documents'):
                                st.write("**Document status:**")
                                    status_str = "✅ downloaded" if doc.get('downloaded') else "❌ failed"
                                st.write(f"- Score: {scoring.get('score')}/100")
                                st.write(f"- Priority tier: {scoring.get('priority_tier')}")
import json
            "company_number": "01234567",
            "company_name": "Example Imports Ltd",
            "sic_codes": "46900; 46420",
            "latest_turnover_gbp": 27500000,
            "providers_found": "HSBC",
            "issues_found": "foreign exchange; cash flow",
            "excerpts": "The group remains exposed to foreign exchange movements and continues to monitor cash flow closely. Banking facilities are currently provided by HSBC.",
            "key_updates": "Expanded into EU supplier base.",
        },
        {
            "company_number": "07654321",
            "company_name": "Local Services Group Ltd",
            "sic_codes": "81210",
            "latest_turnover_gbp": 18000000,
            "providers_found": "",
            "issues_found": "",
            "excerpts": "Operations remain UK-focused with limited exposure to currency risk.",
            "key_updates": "No major treasury changes.",
        },
    ])

                                st.write(f"- Providers detected: {len(extraction.get('providers', []))}")

                            if company.get('report'):
sic_filter = st.sidebar.text_input("SIC code contains")
min_turnover = st.sidebar.number_input("Min turnover (£)", min_value=0.0, value=15000000.0, step=1000000.0)
issue_options = sorted({x for cell in edf["issues_found"].fillna("") for x in split_terms(cell)})
origin_options = sorted({x for cell in edf["issue_origin"].fillna("") for x in split_terms(cell)})
issue_filter = st.sidebar.multiselect("Issues", options=issue_options)
origin_filter = st.sidebar.multiselect("Issue origin", options=origin_options)
provider_filter = st.sidebar.text_input("Provider mentioned")
fit_min = st.sidebar.slider("Min Revolut fit score", 0, 100, 20)

view = edf.copy()
if sic_filter:
    view = view[view["sic_codes"].astype(str).str.contains(sic_filter, case=False, na=False)]
view = view[pd.to_numeric(view["latest_turnover_gbp"], errors="coerce").fillna(0) >= min_turnover]
if issue_filter:
    view = view[view["issues_found"].astype(str).apply(lambda s: any(i.lower() in s.lower() for i in issue_filter))]
if origin_filter:
    view = view[view["issue_origin"].astype(str).apply(lambda s: any(i.lower() in s.lower() for i in origin_filter))]
if provider_filter:
    view = view[view["providers_found"].astype(str).str.contains(provider_filter, case=False, na=False)]
view = view[view["revolut_fit_score"] >= fit_min]

                                st.write("**Structured prospect report:**")
                                report = company.get('report', {})
median_turnover = view["latest_turnover_gbp"].dropna().median() if len(view) and "latest_turnover_gbp" in view else None
c2.metric("Median turnover", f"£{median_turnover:,.0f}" if pd.notna(median_turnover) else "—")
avg_fit = view["revolut_fit_score"].mean() if len(view) else None
c3.metric("Avg fit score", f"{avg_fit:.0f}" if pd.notna(avg_fit) else "—")
provider_count = int(view["providers_found"].fillna("").astype(str).str.len().gt(0).sum()) if len(view) else 0
c4.metric("Provider mentions", provider_count)

                                st.write(f"- Report ID: {report.get('report_id')}")
show_cols = [
    c for c in [
        "company_name",
        "company_number",
        "sic_codes",
        "latest_turnover_gbp",
        "issues_found",
        "issue_origin",
        "providers_found",
        "revolut_fit_score",
        "revolut_fit_notes",
        "key_updates",
        "excerpts",
    ] if c in view.columns
]
                                st.write(f"- Generated at: {report.get('generated_at')}")

                                st.write(f"- Report status: {report.get('status')}")
                                st.write(f"- Document count: {len(report.get('documents', []))}")

                                if report.get('summary'):
extra_fields = [
    "Geography of trading and suppliers, to separate domestic firms from true cross-border needs.",
    "Count of legal entities or subsidiaries, because group complexity raises treasury and spend-control value.",
    "Audit status and filing timeliness, which can hint at process maturity and data reliability.",
    "Employee count band, useful for judging expense-card scale and admin burden.",
    "Existing finance stack mentions such as Xero, NetSuite, Sage, SAP, or payment platforms.",
    "Payment pain signals: slow approvals, manual reconciliation, chargebacks, late supplier payments.",
    "Cash concentration signals: frequent idle cash, low yield, trapped balances, or multi-bank fragmentation.",
    "Growth events: fundraising, acquisitions, new overseas markets, or ERP migrations.",
    "Risk language severity, so you can distinguish a passing mention from a material operational issue.",
]
for item in extra_fields:
    st.write("- " + item)

                                    st.write(f"- Fit score: {report['summary'].get('fit_score')}")
                                    st.write(f"- Priority tier: {report['summary'].get('priority_tier')}")
    "company_number": "",
    "company_name": "",
    "sic_codes": [""],
    "latest_turnover_gbp": 0,
    "filing_date": "",
    "cross_border_exposure": "low|medium|high",
    "issues_found": ["foreign_exchange", "cash_flow"],
    "issue_origin": ["banking", "treasury"],
    "providers_found": ["HSBC", "Xero"],
    "key_updates": ["EU expansion", "new lender"],
    "excerpt_evidence": [{"topic": "fx", "text": "", "source": "accounts 2025"}],
    "revolut_fit_score": 0,
    "revolut_fit_notes": "",
}, indent=2), language="json")
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