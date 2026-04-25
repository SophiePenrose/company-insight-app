from src.extraction.filing_parser import FilingDocument, FilingPage
from src.extraction.base_features import extract_base_features

def test_extract_base_features():
    pages = [FilingPage(page_number=1, text="Revolut reported a loss. Appointment of new director.", blocks=[], tables=[], confidence=1.0, extraction_method="pdf_text")]
    doc = FilingDocument(
        company_number="12345678",
        filing_id="abc123",
        filing_type="AA",
        filing_date="2025-01-01",
        source_url="http://example.com",
        document_hash="deadbeef",
        pipeline_version="v1",
        pages=pages,
        metadata={}
    )
    features = extract_base_features(doc)
    assert "issues_found" in features
    assert "providers_found" in features
    assert "key_updates" in features
    assert "excerpts" in features
    assert "Revolut" in features["providers_found"]
    assert "loss" in features["issues_found"]
    assert any("Appointment of new director" in e for e in features["key_updates"])
