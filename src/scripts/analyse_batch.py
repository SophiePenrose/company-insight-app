import json
import time
from pathlib import Path
from typing import Any, Dict, List

from src.clients.companies_house import CompaniesHouseClient
from src.services.analyser import CompanyAnalyser

ALLOWED_COMPANY_TYPES = {
    "private limited company",
    "public limited company",
    "limited liability partnership",
    "limited partnership",
    "partnership",
}

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

CHECKPOINT_FILE = OUTPUT_DIR / "company_checkpoint.json"
RESULTS_FILE = OUTPUT_DIR / "company_results.jsonl"
CANDIDATES_FILE = OUTPUT_DIR / "company_candidates.jsonl"


def load_checkpoint() -> Dict[str, Any]:
    if CHECKPOINT_FILE.exists():
        return json.loads(CHECKPOINT_FILE.read_text())
    return {"page": 0, "start_index": 0, "completed": False}


def save_checkpoint(page: int, start_index: int, completed: bool = False) -> None:
    CHECKPOINT_FILE.write_text(
        json.dumps(
            {
                "page": page,
                "start_index": start_index,
                "completed": completed,
                "updated_at": time.time(),
            },
            indent=2,
        )
    )


def append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")


def company_type_ok(profile: Dict[str, Any]) -> bool:
    status = str(profile.get("company_status", "")).strip().lower()
    company_type = str(profile.get("type", "")).strip().lower()
    return status == "active" and company_type in ALLOWED_COMPANY_TYPES


def search_candidates(ch_client: CompaniesHouseClient, query: str, pages: int = 5, items_per_page: int = 100) -> List[Dict[str, Any]]:
    results = []
    for page in range(pages):
        start_index = page * items_per_page
        payload = ch_client.search_companies(query=query, items_per_page=items_per_page, start_index=start_index)
        for item in payload.get("items", []):
            results.append(item)
    return results


def main():
    api_key = ""
    query = "b238551e-369b-4407-acfc-0cc3dad71cf2"
    batch_size = 25

    ch_client = CompaniesHouseClient(api_key=api_key)
    analyser = CompanyAnalyser(ch_client=ch_client, matcher_config={})

    checkpoint = load_checkpoint()
    start_page = checkpoint["page"]

    candidates = search_candidates(ch_client, query=query, pages=10, items_per_page=100)

    for candidate in candidates:
        append_jsonl(CANDIDATES_FILE, candidate)

    processed = 0

    for i, candidate in enumerate(candidates):
        if i < start_page:
            continue

        company_number = candidate.get("company_number")
        if not company_number:
            continue

        try:
            profile = ch_client.company_profile(company_number)
            if not company_type_ok(profile):
                continue

            result = analyser.analyse_company(company_number)
            append_jsonl(RESULTS_FILE, result)
            processed += 1

            save_checkpoint(page=i + 1, start_index=i + 1, completed=False)

            if processed % batch_size == 0:
                time.sleep(1)

        except Exception as e:
            append_jsonl(
                RESULTS_FILE,
                {
                    "company_number": company_number,
                    "error": str(e),
                },
            )

    save_checkpoint(page=len(candidates), start_index=len(candidates), completed=True)
    print(f"Done. Processed {processed} companies.")


if __name__ == "__main__":
    main()
