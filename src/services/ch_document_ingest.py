from typing import Any, Dict, List, Optional

from src.clients.companies_house import CompaniesHouseClient
from src.parsing.pdf_text import extract_pdf_text
from src.parsing.ocr import ocr_pdf

import logging

RELEVANT_DOCUMENT_KEYWORDS = [
    "group accounts",
    "annual report",
    "full accounts",
    "strategic report",
    "directors' report",
    "risk",
    "principal activities",
    "note to accounts",
    "accounts with group",
    "accounts-with-accounts-type-full",
    "accounts-with-accounts-type-group",
    "annual accounts",
    "consolidated accounts",
    "micro-entity accounts",
    "micro entity accounts",
    "abridged accounts",
    "dormant accounts",
    "small company accounts",
    "company accounts",
    "accounts",
    "balance sheet",
    "profit and loss",
    "statement of financial position",
    "statement of comprehensive income",
    "financial statements",
    "accounts type",
]

logger = logging.getLogger("ch_document_ingest")
if not logger.hasHandlers():
    import sys
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

import os
from pathlib import Path

def extract_document_text(pdf_bytes: bytes, min_text_chars: int = 200, max_ocr_pages: int = 8, save_sample_pdf: bool = True) -> Dict[str, Any]:
    text = ""
    source = "pdf"
    ocr_used = False
    log_summary = []
    output_dir = Path("output/pdf_samples")
    output_dir.mkdir(parents=True, exist_ok=True)
    # Save the first PDF for manual inspection
    sample_path = output_dir / "sample_filing.pdf"
    if save_sample_pdf and not sample_path.exists():
        try:
            with open(sample_path, "wb") as f:
                f.write(pdf_bytes)
            logger.info(f"Saved sample PDF to {sample_path}")
            log_summary.append(f"Saved sample PDF to {sample_path}")
        except Exception as e:
            logger.error(f"Failed to save sample PDF: {e}")
            log_summary.append(f"Failed to save sample PDF: {e}")

    def is_meaningful(text: str, min_chars: int = 200, min_non_ws: int = 50):
        if not text:
            return False
        non_ws = sum(1 for c in text if not c.isspace())
        if non_ws < min_non_ws:
            return False
        if non_ws / max(len(text), 1) < 0.1:
            return False
        if len(text) < min_chars:
            return False
        return True

    try:
        text = extract_pdf_text(pdf_bytes)
        msg = f"PDF extraction: {len(text)} chars, {sum(1 for c in text if not c.isspace())} non-ws chars"
        logger.info(msg)
        log_summary.append(msg)
    except Exception as e:
        msg = f"PDF extraction error: {e}"
        logger.error(msg)
        log_summary.append(msg)
        text = ""

    if not is_meaningful(text, min_chars=min_text_chars, min_non_ws=50):
        msg = "PDF text not meaningful, triggering OCR fallback."
        logger.info(msg)
        log_summary.append(msg)
        try:
            ocr_text = ocr_pdf(pdf_bytes, max_pages=max_ocr_pages)
            msg = f"OCR extraction: {len(ocr_text)} chars, {sum(1 for c in ocr_text if not c.isspace())} non-ws chars"
            logger.info(msg)
            log_summary.append(msg)
            if ocr_text and is_meaningful(ocr_text, min_chars=100, min_non_ws=20):
                text = ocr_text
                source = "ocr"
                ocr_used = True
            else:
                msg = "OCR text not meaningful or empty."
                logger.warning(msg)
                log_summary.append(msg)
        except Exception as e:
            msg = f"OCR extraction error: {e}"
            logger.error(msg)
            log_summary.append(msg)

    msg = f"Final extracted text source: {source}, ocr_used: {ocr_used}, text length: {len(text)}"
    logger.info(msg)
    log_summary.append(msg)
    return {"text": text or "", "source": source, "ocr_used": ocr_used, "extraction_log": log_summary}


def pick_relevant_filings(filing_items: List[Dict[str, Any]], max_docs: int = 1) -> List[Dict[str, Any]]:
    # 1. Find all filings with 'accounts' in the description
    accounts_filings = [item for item in filing_items if 'accounts' in (item.get('description') or '').lower()]
    if accounts_filings:
        # Sort by date descending (most recent first)
        def get_filing_date(item):
            date = item.get('date') or item.get('transaction_date') or item.get('filing_date')
            return date or ""
        accounts_filings.sort(key=get_filing_date, reverse=True)
        logger.info(f"Found {len(accounts_filings)} filings with 'accounts' in description. Using the latest one: {accounts_filings[0].get('description')} ({get_filing_date(accounts_filings[0])})")
        return [accounts_filings[0]]
    # 2. Fallback: use keyword scoring as before
    scored: List[tuple[int, Dict[str, Any], str]] = []
    for item in filing_items:
        description = (item.get("description") or "")
        description_values = item.get("description_values") or {}
        combined = description + " " + " ".join(str(v) for v in description_values.values())
        matched_keywords = [keyword for keyword in RELEVANT_DOCUMENT_KEYWORDS if keyword in combined.lower()]
        score = len(matched_keywords)
        if score > 0:
            logger.info(f"Filing matched keywords {matched_keywords}: {combined}")
            scored.append((score, item, ", ".join(matched_keywords)))
        else:
            logger.info(f"Filing skipped (no keyword match): {combined}")
    if scored:
        scored.sort(key=lambda pair: pair[0], reverse=True)
        logger.info(f"No 'accounts' filings found, using best keyword match: {scored[0][1].get('description')}")
        return [scored[0][1]]
    # 3. Fallback: just return the first filing
    logger.warning("No relevant filings found by keywords or fallback. Returning first available filing.")
    return filing_items[:1]


def get_document_reference(filing_item: Dict[str, Any]) -> Optional[str]:
    links = filing_item.get("links", {}) or {}
    document_metadata = links.get("document_metadata") or links.get("document")
    if isinstance(document_metadata, str) and document_metadata:
        return document_metadata
    if isinstance(document_metadata, dict):
        return document_metadata.get("href") or document_metadata.get("id")
    return None


def collect_company_documents(
    ch_client: CompaniesHouseClient,
    company_number: str,
    max_docs: int = 10,
    items_per_page: int = 100,
) -> List[Dict[str, Any]]:
    filing_history = ch_client.filing_history(company_number, items_per_page=items_per_page)
    filing_items = filing_history.get("items", []) or []
    relevant_filings = pick_relevant_filings(filing_items, max_docs=max_docs)

    documents: List[Dict[str, Any]] = []
    for filing in relevant_filings:
        document_reference = get_document_reference(filing)
        if not document_reference:
            documents.append(
                {
                    "filing": filing,
                    "document_reference": None,
                    "downloaded": False,
                    "error": "no document metadata available",
                }
            )
            logger.warning(f"No document metadata for filing: {filing.get('description')}")
            continue

        try:
            content_bytes = ch_client.document_content(document_reference)
            extracted = extract_document_text(content_bytes)
            documents.append(
                {
                    "filing": filing,
                    "document_reference": document_reference,
                    "downloaded": True,
                    "text_source": extracted["source"],
                    "ocr_used": extracted["ocr_used"],
                    "extracted_text": extracted["text"],
                }
            )
            logger.info(f"Successfully extracted text from filing: {filing.get('description')}")
        except Exception as exc:
            documents.append(
                {
                    "filing": filing,
                    "document_reference": document_reference,
                    "downloaded": False,
                    "error": str(exc),
                }
            )
            logger.error(f"Failed to extract text from filing: {filing.get('description')}, error: {exc}")

    return documents
