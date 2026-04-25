import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List, Union

from src.fit_scorer.schemas import ExtractionResult, FieldValue, ProviderDetection, RarerInsight


def parse_numeric(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None

    text = text.replace("£", "").replace("GBP", "").replace("gbp", "").replace(",", "")
    text = text.lower()

    match = re.search(r"(\d+(?:\.\d+)?)(?:\s*(bn|b|m|k))?\b", text)
    if not match:
        return None

    value_num = float(match.group(1))
    suffix = match.group(2)
    if suffix:
        if suffix in ("bn", "b"):
            value_num *= 1_000_000_000
        elif suffix == "m":
            value_num *= 1_000_000
        elif suffix == "k":
            value_num *= 1_000

    return value_num


def normalize_text(value: Any) -> str:
    return str(value).strip().lower() if value is not None else ""


def confidence_weight(confidence: str) -> float:
    return {
        "high": 1.0,
        "medium": 0.7,
        "low": 0.4,
    }.get(confidence.lower(), 0.4)


def text_score(value: Any, strong: List[str], moderate: List[str], weak: List[str]) -> float:
    text = normalize_text(value)
    if not text:
        return 0.0

    if any(keyword in text for keyword in strong):
        return 100.0
    if any(keyword in text for keyword in moderate):
        return 70.0
    if any(keyword in text for keyword in weak):
        return 30.0
    return 50.0


def score_turnover(field: FieldValue) -> float:
    turnover = parse_numeric(field.value)
    if turnover is None:
        return 0.0

    if turnover >= 100_000_000:
        return 100.0
    if turnover >= 50_000_000:
        return 90.0
    if turnover >= 20_000_000:
        return 80.0
    if turnover >= 10_000_000:
        return 70.0
    if turnover >= 5_000_000:
        return 55.0
    if turnover >= 1_000_000:
        return 35.0
    return 15.0


def score_fx_intensity(field: FieldValue) -> float:
    return text_score(
        field.value,
        strong=["high", "strong", "significant", "intense", "substantial", "international", "cross-border"],
        moderate=["medium", "moderate", "some", "occasional", "cross border", "global"],
        weak=["low", "limited", "minimal", "small"],
    ) * confidence_weight(field.confidence)


def score_payments_acceptance(field: FieldValue) -> float:
    return text_score(
        field.value,
        strong=["online", "ecommerce", "card", "digital", "payment platform", "payment acceptance", "contactless", "mobile", "api"],
        moderate=["bank transfer", "bacs", "direct debit", "swift", "wire", "cheque"],
        weak=["cash", "paper", "manual", "postal"],
    ) * confidence_weight(field.confidence)


def score_spend_profile(field: FieldValue) -> float:
    return text_score(
        field.value,
        strong=["high spend", "large spend", "corporate spend", "vendor spend", "purchase volume", "capex", "strategic spend"],
        moderate=["regular spend", "operational spend", "expense management", "procurement"],
        weak=["low spend", "occasional spend", "ad hoc"],
    ) * confidence_weight(field.confidence)


def score_ap_payroll_complexity(field: FieldValue) -> float:
    return text_score(
        field.value,
        strong=["complex payroll", "multiple payroll providers", "multi-jurisdiction", "contractor", "agency workers", "bureau", "payroll complexity", "outsourced payroll"],
        moderate=["payroll", "payroll processing", "payroll run", "tax and payroll"],
        weak=["simple payroll", "small payroll", "in-house payroll", "one payroll"],
    ) * confidence_weight(field.confidence)


def score_tech_stack(field: FieldValue) -> float:
    return text_score(
        field.value,
        strong=["sap", "oracle", "netsuite", "workday", "stripe", "adyen", "salesforce", "sage", "xero", "quickbooks", "dynamics", "cloud", "api", "integrated", "digital"],
        moderate=["platform", "software", "system", "online", "modern"],
        weak=["legacy", "manual", "paper", "offline"],
    ) * confidence_weight(field.confidence)


def score_triggers(field: FieldValue) -> float:
    return text_score(
        field.value,
        strong=["expansion", "growth", "acquisition", "new market", "investment", "funding", "ipo", "restructure", "divestment", "launch", "scale"],
        moderate=["review", "planning", "strategy", "initiative", "transformation", "digital"],
        weak=["maintenance", "status quo", "steady", "stable"],
    ) * confidence_weight(field.confidence)


def score_rarer_insights(insights: List[RarerInsight]) -> float:
    if not insights:
        return 0.0

    score = sum(min(max(insight.strength_1_to_5, 1), 5) * 20 for insight in insights)
    return min(score / len(insights), 100.0)


def recency_bonus(document_dates: List[str]) -> float:
    """Add bonus for recent documents. Max 10 points if most recent is within 6 months."""
    if not document_dates:
        return 0.0
    try:
        dates = [datetime.fromisoformat(date.replace('Z', '+00:00')) for date in document_dates if date]
        if not dates:
            return 0.0
        most_recent = max(dates)
        now = datetime.utcnow()
        months_old = (now - most_recent).days / 30
        if months_old <= 6:
            return 10.0
        elif months_old <= 12:
            return 5.0
        return 0.0
    except ValueError:
        return 0.0


def score_providers(providers: List[ProviderDetection]) -> float:
    if not providers:
        return 0.0

    categories = [provider.category for provider in providers]
    if any(category in ["psp", "erp", "expenses", "payroll_eor"] for category in categories):
        return 100.0
    if any(category in ["ecom", "treasury"] for category in categories):
        return 80.0
    if any(category == "bank" for category in categories):
        return 50.0
    return 40.0


def aggregate_score(component_scores: Dict[str, float], weights: Dict[str, float]) -> float:
    total = 0.0
    for key, score in component_scores.items():
        total += score * weights.get(key, 0.0)
    return min(total, 100.0)


def assign_priority_tier(score: float) -> str:
    if score >= 75:
        return "tier_1"
    if score >= 50:
        return "tier_2"
    return "tier_3"


def explain_component(field_name: str, field: FieldValue, score: float) -> Dict[str, Any]:
    label = field_name.replace("_", " ").title()
    quote = None
    if field.evidence:
        quote = field.evidence[0].quote
    elif field.value:
        quote = str(field.value)

    if not quote:
        explanation = f"No evidence was extracted for {label}. Score {score:.1f}."
    else:
        explanation = f"{label} scored {score:.1f} based on extracted evidence: '{quote}'."

    return {
        "component": field_name,
        "value": field.value,
        "confidence": field.confidence,
        "score": round(score, 1),
        "explanation": explanation,
    }


def build_score_summary(component_scores: Dict[str, float]) -> str:
    sorted_scores = sorted(component_scores.items(), key=lambda item: item[1], reverse=True)
    top_components = [f"{name} ({score:.0f})" for name, score in sorted_scores[:3] if score > 0]
    if not top_components:
        return "No significant scoring drivers were detected."
    return "Top scoring signals: " + ", ".join(top_components) + "."


def score_confidence(extraction: ExtractionResult) -> str:
    fields = [
        extraction.turnover_gbp,
        extraction.fx_intensity,
        extraction.payments_acceptance,
        extraction.spend_profile,
        extraction.ap_payroll_complexity,
        extraction.tech_stack,
        extraction.triggers,
    ]
    weights = [confidence_weight(f.confidence) for f in fields if f is not None]
    if not weights:
        return "low"
    avg = sum(weights) / len(weights)
    if avg >= 0.85:
        return "high"
    if avg >= 0.6:
        return "medium"
    return "low"


def score_extraction_result(extraction: Union[ExtractionResult, Dict[str, Any]], document_dates: Optional[List[str]] = None) -> Dict[str, Any]:
    if isinstance(extraction, dict):
        extraction_obj = ExtractionResult.model_validate(extraction)
    else:
        extraction_obj = extraction

    component_scores = {
        "turnover": score_turnover(extraction_obj.turnover_gbp),
        "fx_intensity": score_fx_intensity(extraction_obj.fx_intensity),
        "payments_acceptance": score_payments_acceptance(extraction_obj.payments_acceptance),
        "spend_profile": score_spend_profile(extraction_obj.spend_profile),
        "ap_payroll_complexity": score_ap_payroll_complexity(extraction_obj.ap_payroll_complexity),
        "tech_stack": score_tech_stack(extraction_obj.tech_stack),
        "triggers": score_triggers(extraction_obj.triggers),
        "rarer_insights": score_rarer_insights(extraction_obj.rarer_insights),
        "providers": score_providers(extraction_obj.providers),
    }

    weights = {
        "turnover": 0.18,
        "fx_intensity": 0.14,
        "payments_acceptance": 0.12,
        "spend_profile": 0.12,
        "ap_payroll_complexity": 0.12,
        "tech_stack": 0.10,
        "triggers": 0.10,
        "rarer_insights": 0.10,  # Increased from 0.08
        "providers": 0.02,  # Adjusted to balance
    }

    score = aggregate_score(component_scores, weights)
    recency = recency_bonus(document_dates or [])
    score = min(score + recency, 100.0)

    confidence = score_confidence(extraction_obj)
    priority_tier = assign_priority_tier(score)

    explanations = [
        explain_component("turnover", extraction_obj.turnover_gbp, component_scores["turnover"]),
        explain_component("fx_intensity", extraction_obj.fx_intensity, component_scores["fx_intensity"]),
        explain_component("payments_acceptance", extraction_obj.payments_acceptance, component_scores["payments_acceptance"]),
        explain_component("spend_profile", extraction_obj.spend_profile, component_scores["spend_profile"]),
        explain_component("ap_payroll_complexity", extraction_obj.ap_payroll_complexity, component_scores["ap_payroll_complexity"]),
        explain_component("tech_stack", extraction_obj.tech_stack, component_scores["tech_stack"]),
        explain_component("triggers", extraction_obj.triggers, component_scores["triggers"]),
        {
            "component": "rarer_insights",
            "value": [insight.insight for insight in extraction_obj.rarer_insights],
            "confidence": "high" if extraction_obj.rarer_insights else "low",
            "score": round(component_scores["rarer_insights"], 1),
            "explanation": f"Rarer insights contributed {component_scores['rarer_insights']:.1f} points.",
        },
        {
            "component": "providers",
            "value": [provider.provider for provider in extraction_obj.providers],
            "confidence": "high" if extraction_obj.providers else "low",
            "score": round(component_scores["providers"], 1),
            "explanation": f"Provider detection contributed {component_scores['providers']:.1f} points.",
        },
    ]

    return {
        "score": round(score, 1),
        "priority_tier": priority_tier,
        "confidence": confidence,
        "breakdown": component_scores,
        "explanations": explanations,
        "summary": build_score_summary(component_scores),
    }
