import pytest

from src.fit_scorer.scoring import score_extraction_result


def test_score_extraction_result_high_fit():
    extraction = {
        "company_name": {"value": "Test Co", "confidence": "high", "evidence": []},
        "turnover_gbp": {"value": "£120,000,000", "confidence": "high", "evidence": []},
        "employees": {"value": "320", "confidence": "high", "evidence": []},
        "industry": {"value": "ecommerce", "confidence": "high", "evidence": []},
        "business_model": {"value": "ecommerce", "confidence": "high", "evidence": []},
        "geos": {"value": "UK, EU", "confidence": "high", "evidence": []},
        "fx_intensity": {"value": "high international sales", "confidence": "high", "evidence": []},
        "payments_acceptance": {"value": "online card payments", "confidence": "high", "evidence": []},
        "spend_profile": {"value": "large corporate spend", "confidence": "high", "evidence": []},
        "ap_payroll_complexity": {"value": "complex payroll with contractors and bureau", "confidence": "high", "evidence": []},
        "tech_stack": {"value": "Stripe, AWS, Salesforce", "confidence": "high", "evidence": []},
        "triggers": {"value": "growth and expansion into new markets", "confidence": "high", "evidence": []},
        "rarer_insights": [
            {"type": "goal", "insight": "Expand cross-border ecommerce", "strength_1_to_5": 5, "evidence": {"quote": "expand into EU", "source": "filing"}}
        ],
        "providers": [
            {"provider": "Stripe", "category": "psp", "detected_as": "explicit", "confidence": "high", "evidence": []}
        ]
    }

    result = score_extraction_result(extraction)
    assert result["score"] >= 80
    assert result["priority_tier"] == "tier_1"
    assert result["confidence"] == "high"


def test_score_extraction_result_low_fit():
    extraction = {
        "company_name": {"value": "Small Co", "confidence": "low", "evidence": []},
        "turnover_gbp": {"value": "£300,000", "confidence": "low", "evidence": []},
        "employees": {"value": "12", "confidence": "low", "evidence": []},
        "industry": {"value": "retail", "confidence": "low", "evidence": []},
        "business_model": {"value": "brick and mortar", "confidence": "low", "evidence": []},
        "geos": {"value": "UK", "confidence": "low", "evidence": []},
        "fx_intensity": {"value": "low", "confidence": "low", "evidence": []},
        "payments_acceptance": {"value": "cash and cheque", "confidence": "low", "evidence": []},
        "spend_profile": {"value": "small occasional spend", "confidence": "low", "evidence": []},
        "ap_payroll_complexity": {"value": "simple in-house payroll", "confidence": "low", "evidence": []},
        "tech_stack": {"value": "none", "confidence": "low", "evidence": []},
        "triggers": {"value": "steady state", "confidence": "low", "evidence": []},
        "rarer_insights": [],
        "providers": []
    }

    result = score_extraction_result(extraction)
    assert result["score"] < 40
    assert result["priority_tier"] == "tier_3"
    assert result["confidence"] == "low"
    assert "explanations" in result
    assert len(result["explanations"]) >= 1
