from src.extraction.filing_parser import FilingDocument, FilingPage, parse_pdf
import pytest

def test_parse_pdf_text():
    # Use a small sample PDF file for testing
    with open("tests/sample.pdf", "rb") as f:
        pdf_bytes = f.read()
    pages = parse_pdf(pdf_bytes)
    assert isinstance(pages, list)
    assert all(isinstance(p, FilingPage) for p in pages)
    assert all(p.text is not None for p in pages)

def test_filing_document_to_json():
    doc = FilingDocument(
        company_number="12345678",
        filing_id="abc123",
        filing_type="AA",
        filing_date="2025-01-01",
        source_url="http://example.com",
        document_hash="deadbeef",
        pipeline_version="v1",
        pages=[],
        metadata={}
    )
    json_str = doc.to_json()
    assert "company_number" in json_str
    assert "filing_id" in json_str
