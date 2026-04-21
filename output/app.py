from pathlib import Path
text = '''import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.clients.companies_house import CompaniesHouseClient
from src.services.analyser import CompanyAnalyser

st.set_page_config(page_title="Company Insight Screener", layout="wide")

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
CHECKPOINT_FILE = OUTPUT_DIR / "company_checkpoint.json"
RESULTS_FILE = OUTPUT_DIR / "company_results.jsonl"
CANDIDATES_FILE = OUTPUT_DIR / "company_candidates.jsonl"

ALLOWED_COMPANY_TYPES = {
    "private limited company",
    "public limited company",
    "limited liability partnership",
    "limited partnership",
    "partnership",
}


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


def load_checkpoint():
    if CHECKPOINT_FILE.exists():
        return json.loads(CHECKPOINT_FILE.read_text())
    return {"processed": 0, "completed": False, "query": ""}


def save_checkpoint(processed: int, completed: bool, query: str):
    CHECKPOINT_FILE.write_text(json.dumps({"processed": processed, "completed": completed, "query": query}, indent=2))


st.title("Company Insight Screener")
st.caption("Build a company list from Companies House, then analyse new filings over time.")

with st.sidebar:
    st.header("Companies House")
    api_key = st.text_input("Companies House API key", type="password")
    query = st.text_input("Search query", value="company")
    batch_size = st.number_input("Batch size", min_value=1, max_value=500, value=25, step=5)
    build_clicked = st.button("Build company list")
    resume_clicked = st.button("Resume analysis")
    clear_clicked = st.button("Clear saved files")

if clear_clicked:
    for path in [CHECKPOINT_FILE, RESULTS_FILE, CANDIDATES_FILE]:
        if path.exists():
            path.unlink()
    st.success("Cleared saved files")
    st.stop()

checkpoint = load_checkpoint()
results = load_jsonl(RESULTS_FILE)
candidates = load_jsonl(CANDIDATES_FILE)

st.metric("Saved candidates", len(candidates))
st.metric("Saved results", len(results))
st.metric("Last processed", checkpoint.get("processed", 0))

if build_clicked or resume_clicked:
    if not api_key:
        st.error("Add your Companies House API key first.")
        st.stop()

    ch_client = CompaniesHouseClient(api_key=api_key)
    analyser = CompanyAnalyser(ch_client=ch_client, matcher_config={})

    if build_clicked:
        st.write("Searching Companies House...")
        payload = ch_client.search_companies(query=query, items_per_page=100, start_index=0)
        items = payload.get("items", [])
        if not items:
            st.warning("No companies found.")
            st.stop()
        with CANDIDATES_FILE.open("w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item) + "\n")
        save_checkpoint(processed=0, completed=False, query=query)
        st.success(f"Saved {len(items)} candidates.")
        st.stop()

    if resume_clicked:
        if not CANDIDATES_FILE.exists():
            st.error("No saved candidates yet. Click Build company list first.")
            st.stop()

        candidate_rows = load_jsonl(CANDIDATES_FILE)
        start = int(checkpoint.get("processed", 0))
        progress = st.progress(0)
        status = st.empty()

        for idx in range(start, min(start + int(batch_size), len(candidate_rows))):
            candidate = candidate_rows[idx]
            company_number = candidate.get("company_number")
            if not company_number:
                continue
            status.write(f"Analysing {idx + 1}/{len(candidate_rows)}: {company_number}")
            try:
                result = analyser.analyse_company(company_number)
                append_jsonl(RESULTS_FILE, result)
            except Exception as e:
                append_jsonl(RESULTS_FILE, {"company_number": company_number, "error": str(e)})
            progress.progress((idx + 1) / len(candidate_rows))
            save_checkpoint(processed=idx + 1, completed=(idx + 1) >= len(candidate_rows), query=checkpoint.get("query", query))

        st.success("Batch finished. Run Resume analysis again to continue.")
        st.stop()

st.subheader("Saved results")
if results:
    df = pd.DataFrame(results)
    st.dataframe(df, use_container_width=True, height=500)
else:
    st.info("No saved results yet.")
'''
Path('output').mkdir(exist_ok=True)
Path('output/app.py').write_text(text)
print('updated output/app.py')
