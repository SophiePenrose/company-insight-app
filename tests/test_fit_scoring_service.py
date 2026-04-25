from src.services.fit_scoring_service import FitScoringService, FitScoreResult
from src.extraction.filing_parser import FilingDocument, FilingPage
from src.extraction.base_features import extract_base_features
import os

def test_fit_scoring_service_stub(monkeypatch):
    # Patch call_llm_api to return a stub response
    monkeypatch.setenv("OPENAI_API_KEY", "stub")
    from src.services import gemini_fit
    monkeypatch.setattr(gemini_fit, "call_llm_api", lambda *a, **kw: '{"segment_fit": {"why_we_win": 10, "green_flags": 10, "red_flags": 2, "confidence": "direct"}, "timing_modifier": {"score": 5, "reason": "expansion", "confidence": "direct"}, "competitive_modifier": {"score": 5, "reason": "incumbent", "confidence": "direct"}, "other_pillars": {"payments": 8, "fx": 9, "expenses": 6, "billpay": 5, "confidence": "proxy"}, "prohibited": false}')
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
    base_features = extract_base_features(doc)
    service = FitScoringService(model_name="stub", prompt_version="test", pipeline_version="test")
    result = service.score(doc, base_features)
    assert isinstance(result, FitScoreResult)
    assert result.scores["overall_score"] > 0
    assert result.model_name == "stub"
