from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

import hashlib
import requests
import fitz  # PyMuPDF
import pytesseract
from pathlib import Path
import io
import json
import logging

logger = logging.getLogger("filing_parser")
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

@dataclass
class FilingPage:
    page_number: int
    text: str
    blocks: List[Dict[str, Any]]
    tables: List[Dict[str, Any]]
    confidence: float
    extraction_method: str  # 'xbrl', 'pdf_text', 'pdf_ocr'

@dataclass
class FilingDocument:
    company_number: str
    filing_id: str
    filing_type: str
    filing_date: str
    source_url: str
    document_hash: str
    pipeline_version: str
    pages: List[FilingPage]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json(self):
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

# --- Main parser logic ---
def download_filing_pdf(url: str) -> bytes:
    if not url or not isinstance(url, str) or not url.lower().startswith("http"):
        logger.error(f"Invalid or missing source_url: {url}")
        raise ValueError(f"Invalid or missing source_url: {url}")
    logger.info(f"Downloading filing PDF from {url}")
    resp = requests.get(url)
    logger.info(f"HTTP status: {resp.status_code}, Content-Type: {resp.headers.get('Content-Type')}, Size: {len(resp.content)} bytes")
    resp.raise_for_status()
    if not resp.content or len(resp.content) < 1000:
        logger.error(f"Downloaded file is empty or too small: {len(resp.content)} bytes from {url}")
        raise ValueError(f"Downloaded file is empty or too small: {len(resp.content)} bytes from {url}")
    if 'pdf' not in resp.headers.get('Content-Type', '').lower():
        logger.error(f"Downloaded file is not a PDF. Content-Type: {resp.headers.get('Content-Type')}")
        raise ValueError(f"Downloaded file is not a PDF. Content-Type: {resp.headers.get('Content-Type')}")
    logger.info(f"Downloaded {len(resp.content)} bytes from {url}")
    return resp.content

def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def parse_pdf(pdf_bytes: bytes) -> List[FilingPage]:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        logger.error(f"Failed to open PDF: {e}")
        raise
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        blocks = page.get_text("blocks")
        tables = []  # Table extraction can be added here
        extraction_method = 'pdf_text'
        confidence = 1.0 if text.strip() else 0.0
        logger.info(f"Page {i+1}: extracted {len(text.strip())} chars with pdf_text.")
        # OCR fallback for image-only pages
        if not text.strip():
            logger.info(f"Page {i+1}: No text found, attempting OCR fallback.")
            try:
                pix = page.get_pixmap()
                img_bytes = pix.tobytes()
                img = io.BytesIO(img_bytes)
                ocr_text = pytesseract.image_to_string(img)
                text = ocr_text
                extraction_method = 'pdf_ocr'
                confidence = 0.6 if ocr_text.strip() else 0.0
                logger.info(f"Page {i+1}: OCR extracted {len(ocr_text.strip())} chars.")
            except Exception as e:
                logger.error(f"Page {i+1}: OCR failed: {e}")
        pages.append(FilingPage(
            page_number=i+1,
            text=text,
            blocks=blocks,
            tables=tables,
            confidence=confidence,
            extraction_method=extraction_method
        ))
    return pages

# XBRL/iXBRL parsing stub (to be implemented)
def parse_xbrl(xbrl_bytes: bytes) -> List[FilingPage]:
    # TODO: Implement XBRL/iXBRL parsing for structured data
    return []

def parse_filing(company_number: str, filing_id: str, filing_type: str, filing_date: str, source_url: str, pipeline_version: str, metadata: dict = None) -> FilingDocument:
    pdf_bytes = download_filing_pdf(source_url)
    document_hash = hash_bytes(pdf_bytes)
    # TODO: Add logic to prefer XBRL/iXBRL if available
    pages = parse_pdf(pdf_bytes)
    total_text = sum(len(p.text.strip()) for p in pages)
    logger.info(f"Total extracted text length: {total_text} chars across {len(pages)} pages.")
    if total_text == 0:
        logger.error("No document text available for extraction after all methods.")
        # Save problematic PDF for inspection
        debug_dir = Path("output/problem_pdfs")
        debug_dir.mkdir(parents=True, exist_ok=True)
        debug_path = debug_dir / f"{company_number}_{filing_id or 'nofiling'}_{document_hash[:8]}.pdf"
        with open(debug_path, "wb") as f:
            f.write(pdf_bytes)
        logger.error(f"Saved problematic PDF to {debug_path}")
        raise ValueError(f"Extraction pipeline error: No document text available for extraction. PDF saved to {debug_path}")
    return FilingDocument(
        company_number=company_number,
        filing_id=filing_id,
        filing_type=filing_type,
        filing_date=filing_date,
        source_url=source_url,
        document_hash=document_hash,
        pipeline_version=pipeline_version,
        pages=pages,
        metadata=metadata or {}
    )
