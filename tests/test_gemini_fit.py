import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from src.services.gemini_fit import (
    parse_gemini_response,
    is_prohibited_company,
    calculate_overall_fit_score,
    compute_osint_fit_score,
)

def test_prohibited_company_exclusion():
    stub_response = '''{
      "prohibited": true,
      "prohibited_reason": "Nature of business: Cryptocurrency exchange (SIC 66110)",
      "prohibited_source": "Companies House filing"
    }'''
    gemini_result = parse_gemini_response(stub_response)
    assert is_prohibited_company(gemini_result)
    assert gemini_result["prohibited_reason"].startswith("Nature of business")

def test_high_fit_score():
    evidence = {
        "fx_exposure": [(1.0, 1.0, "Strong FX evidence")],
        "product_wedge": [(1.0, 1.0, "Clear product wedge")],
        "delegation_complexity": [(1.0, 1.0, "Complex delegation")],
        "multi_entity": [(1.0, 1.0, "Multiple entities")],
        "expansion_trigger": [(1.0, 1.0, "Expansion event")],
        "cost_pressure": [(1.0, 1.0, "Cost pressure")],
        "stakeholders_identifiable": [(1.0, 1.0, "Stakeholders found")],
        "evidence_pain_solution": [(1.0, 1.0, "Pain solution evident")],
    }
    score, trace, completeness = compute_osint_fit_score(evidence)
    assert score > 80
    assert completeness > 0.5
    assert "fx_exposure" in trace

def test_low_fit_score():
    evidence = {
        "fx_exposure": [(0.0, 1.0, "No FX evidence")],
        "product_wedge": [(0.0, 1.0, "No wedge")],
        "delegation_complexity": [(0.0, 1.0, "No delegation")],
        "multi_entity": [(0.0, 1.0, "No entities")],
        "expansion_trigger": [(0.0, 1.0, "No expansion")],
        "cost_pressure": [(0.0, 1.0, "No cost pressure")],
        "stakeholders_identifiable": [(0.0, 1.0, "No stakeholders")],
        "evidence_pain_solution": [(0.0, 1.0, "No pain solution")],
    }
    score, trace, completeness = compute_osint_fit_score(evidence)
    assert score < 40
    assert completeness > 0.5

def test_incomplete_profile():
    evidence = {
        "fx_exposure": [(1.0, 1.0, "Strong FX evidence")],
        # All other indicators missing
    }
    score, trace, completeness = compute_osint_fit_score(evidence)
    assert 0 < score < 40
    assert completeness < 0.3
    assert "fx_exposure" in trace
