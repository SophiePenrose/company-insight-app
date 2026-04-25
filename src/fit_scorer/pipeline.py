from typing import Dict, Any, List

from typing import Dict, Any, List

from src.clients.companies_house import CompaniesHouseClient
from src.services.ch_document_ingest import collect_company_documents
from src.fit_scorer.llm.extractors import extract_structured
from src.fit_scorer.scoring import score_extraction_result
from src.fit_scorer.report import build_prospect_report


def run_company_extraction(
    ch_client: CompaniesHouseClient,
    company_number: str,
    company_name: str,
    company_profile: dict,
    max_docs: int = 2,
    model: str | None = None,
) -> Dict[str, Any]:
    documents = collect_company_documents(ch_client, company_number, max_docs=max_docs)
    extraction = None
    extraction_error = None
    scoring = None
    report = None

    try:
        extraction = extract_structured(company_name, documents, model=model)
        if extraction is None:
            raise ValueError("extract_structured returned None")
        document_dates = [doc.get("filing", {{}}).get("date") for doc in documents if doc.get("filing", {{}}).get("date")]
        scoring = score_extraction_result(extraction, document_dates)
        report = build_prospect_report(
            company_number=company_number,
            company_name=company_name,
            profile=company_profile,
            documents=documents,
            extraction=extraction.dict() if hasattr(extraction, 'dict') else extraction,
            scoring=scoring,
        )
    except Exception as exc:
        extraction_error = f"Extraction pipeline error: {exc}"
        print(f"[Extraction Error] {extraction_error}")
        report = build_prospect_report(
            company_number=company_number,
            company_name=company_name,
            profile=company_profile,
            documents=documents,
            extraction=None,
            scoring=None,
            extraction_error=extraction_error,
        )

    return {
        "company_number": company_number,
        "company_name": company_name,
        "documents": documents,
        "extraction": extraction.dict() if extraction else None,
        "extraction_error": extraction_error,
        "scoring": scoring,
        "report": report,
    }
