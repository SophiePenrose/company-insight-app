from src.fit_scorer.report import build_prospect_report


def test_build_prospect_report_includes_metadata_and_audit_trail():
    profile = {
        "company_number": "01234567",
        "company_name": "Test Prospect Ltd",
        "company_status": "active",
        "type": "ltd",
        "date_of_creation": "2020-01-01",
        "registered_office_address": {"address_line_1": "1 Test Street"},
        "sic_codes": [62020],
    }
    documents = [
        {
            "filing": {"description": "Group accounts", "date": "2024-04-01"},
            "document_reference": "ABC123",
            "downloaded": True,
            "text_source": "pdf",
            "ocr_used": False,
            "extracted_text": "This is a test document.",
        }
    ]
    extraction = {"company_name": {"value": "Test Prospect Ltd", "confidence": "high", "evidence": []}}
    scoring = {"score": 87, "priority_tier": "tier_1", "confidence": "high", "summary": "Good fit"}

    report = build_prospect_report(
        company_number="01234567",
        company_name="Test Prospect Ltd",
        profile=profile,
        documents=documents,
        extraction=extraction,
        scoring=scoring,
    )

    assert report["company_number"] == "01234567"
    assert report["company_name"] == "Test Prospect Ltd"
    assert report["profile"]["company_status"] == "active"
    assert report["documents"][0]["filing_description"] == "Group accounts"
    assert report["summary"]["fit_score"] == 87
    assert report["status"] == "success"
    assert any(event["event_type"] == "scoring_completed" for event in report["audit_trail"])
    assert "company_summary" in report
    assert "pain_points" in report
    assert "revolut_opportunity" in report
    assert report["revolut_opportunity"]["pitch_summary"].startswith("This")
    assert len(report["revolut_opportunity"]["recommended_use_cases"]) > 0
