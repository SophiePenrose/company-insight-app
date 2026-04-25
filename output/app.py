import json
import re
from typing import Dict, List

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Company Insight Screener", layout="wide")

DEFAULT_ISSUE_KEYWORDS = {
    "foreign_exchange": ["foreign exchange", "foreign currency", "exchange rate risk", "currency risk", "fx"],
    "cash_flow": ["cash flow", "working capital", "liquidity", "short-term funding"],
    "banking": ["banking", "bank facilities", "lender", "loan covenant", "overdraft", "HSBC", "Barclays", "NatWest", "Lloyds"],
    "savings_yield": ["interest income", "deposit rates", "return on cash", "savings rate"],
}

REVOLUT_SIGNALS = {
    "multi_currency_need": ["foreign exchange", "foreign currency", "exchange rate risk", "international supplier", "overseas supplier"],
    "expense_cards_need": ["employee spend", "expenses", "corporate card", "virtual card", "travel expense"],
    "banking_pain": ["slow payments", "banking", "manual payments", "legacy bank", "bank charges"],
    "api_need": ["api", "automation", "erp", "integration", "xero", "netsuite", "batch payments"],
    "treasury_need": ["idle cash", "cash management", "liquidity", "yield on cash"],
}


def split_terms(text: str) -> List[str]:
    return [t.strip() for t in re.split(r"[;,|]", str(text)) if t.strip()]


def detect_keywords(text: str, mapping: Dict[str, List[str]]) -> Dict[str, List[str]]:
    lower = text.lower()
    found = {}
    for label, kws in mapping.items():
        hits = [kw for kw in kws if kw.lower() in lower]
        if hits:
            found[label] = hits
    return found


def infer_revolut_fit(excerpts: str, providers: str, issues: str) -> Dict[str, str]:
    corpus = " ".join([str(excerpts), str(providers), str(issues)])
    hits = detect_keywords(corpus, REVOLUT_SIGNALS)
    score = 0
    notes = []
    if "multi_currency_need" in hits:
        score += 30
        notes.append("Multi-currency or FX need detected")
    if "expense_cards_need" in hits:
        score += 20
        notes.append("Expense-card workflow likely relevant")
    if "banking_pain" in hits:
        score += 20
        notes.append("Banking friction mentioned")
    if "api_need" in hits:
        score += 15
        notes.append("Automation/API signals present")
    if "treasury_need" in hits:
        score += 15
        notes.append("Cash-management or yield signal present")
    if re.search(r"\b(HSBC|Barclays|NatWest|Lloyds|Santander)\b", providers, re.I):
        notes.append("Incumbent provider mentioned")
    return {
        "score": min(score, 100),
        "notes": "; ".join(notes) if notes else "Limited explicit fit signals in current text",
    }


def enrich_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    defaults = {
        "excerpts": "",
        "providers_found": "",
        "issues_found": "",
        "issue_origin": "",
        "key_updates": "",
        "sic_codes": "",
        "latest_turnover_gbp": None,
        "company_name": "",
        "company_number": "",
    }
    for col, val in defaults.items():
        if col not in df.columns:
            df[col] = val

    auto_issues = []
    auto_origins = []
    fit_scores = []
    fit_notes = []

    for _, row in df.iterrows():
        text = " ".join([str(row.get("issues_found", "")), str(row.get("excerpts", "")), str(row.get("key_updates", ""))])
        issue_hits = detect_keywords(text, DEFAULT_ISSUE_KEYWORDS)
        auto_issues.append(", ".join(sorted(issue_hits.keys())) if issue_hits else str(row.get("issues_found", "")))

        origins = []
        if "banking" in issue_hits:
            origins.append("banking")
        if "foreign_exchange" in issue_hits:
            origins.append("cross-border / FX")
        if "cash_flow" in issue_hits:
            origins.append("cash flow / liquidity")
        if "savings_yield" in issue_hits:
            origins.append("treasury / cash returns")
        auto_origins.append(", ".join(origins) if origins else str(row.get("issue_origin", "")))

        fit = infer_revolut_fit(str(row.get("excerpts", "")), str(row.get("providers_found", "")), str(row.get("issues_found", "")))
        fit_scores.append(fit["score"])
        fit_notes.append(fit["notes"])

    df["issues_found"] = auto_issues
    df["issue_origin"] = auto_origins
    df["revolut_fit_score"] = fit_scores
    df["revolut_fit_notes"] = fit_notes
    return df


st.title("Company Insight Screener")
st.caption("Upload a CSV of Companies House / account-screening results, then filter and score for Revolut Business fit.")

with st.sidebar:
    st.header("Inputs")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    st.markdown(
        "Expected useful columns: company_number, company_name, sic_codes, latest_turnover_gbp, "
        "issues_found, issue_origin, providers_found, excerpts, key_updates."
    )

if uploaded:
    df = pd.read_csv(uploaded)
else:
    df = pd.DataFrame([
        {
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

edf = enrich_df(df)

st.sidebar.header("Filters")
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

c1, c2, c3, c4 = st.columns(4)
c1.metric("Companies", len(view))
median_turnover = view["latest_turnover_gbp"].dropna().median() if len(view) and "latest_turnover_gbp" in view else None
c2.metric("Median turnover", f"£{median_turnover:,.0f}" if pd.notna(median_turnover) else "—")
avg_fit = view["revolut_fit_score"].mean() if len(view) else None
c3.metric("Avg fit score", f"{avg_fit:.0f}" if pd.notna(avg_fit) else "—")
provider_count = int(view["providers_found"].fillna("").astype(str).str.len().gt(0).sum()) if len(view) else 0
c4.metric("Provider mentions", provider_count)

st.subheader("Screened companies")
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
st.dataframe(view[show_cols], use_container_width=True, height=520)

csv = view.to_csv(index=False).encode("utf-8")
st.download_button("Download filtered CSV", csv, file_name="company_insight_screen.csv", mime="text/csv")

st.subheader("Helpful extra fields to add")
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

st.subheader("Suggested target schema")
st.code(json.dumps({
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
