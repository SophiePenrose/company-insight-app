from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.fit_scorer.schemas import ExtractionResult


def build_company_url(company_number: str) -> str:
    return f"https://find-and-update.company-information.service.gov.uk/company/{company_number}"


def build_document_url(document_reference: Optional[str]) -> Optional[str]:
    if not document_reference:
        return None
    if document_reference.startswith("http"):
        return document_reference
    if document_reference.startswith("/document/"):
        return f"https://document-api.company-information.service.gov.uk{document_reference}"
    return f"https://document-api.company-information.service.gov.uk/document/{document_reference}/content"


def summarize_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "company_number": profile.get("company_number"),
        "company_name": profile.get("company_name"),
        "company_status": profile.get("company_status"),
        "company_type": profile.get("type"),
        "date_of_creation": profile.get("date_of_creation"),
        "registered_office_address": profile.get("registered_office_address"),
        "sic_codes": profile.get("sic_codes"),
        "industry_codes": profile.get("sic_codes"),
    }


def extract_document_metadata(doc: Dict[str, Any]) -> Dict[str, Any]:
    filing = doc.get("filing", {}) or {}
    metadata = {
        "filing_description": filing.get("description"),
        "filing_date": filing.get("date"),
        "filing_id": filing.get("transaction_id") or filing.get("barcode") or filing.get("postal_code"),
        "document_reference": doc.get("document_reference"),
        "document_url": build_document_url(doc.get("document_reference")),
        "downloaded": doc.get("downloaded", False),
        "text_source": doc.get("text_source"),
        "ocr_used": doc.get("ocr_used", False),
        "extracted_text_length": len(doc.get("extracted_text", "")) if doc.get("extracted_text") else 0,
        "error": doc.get("error"),
    }
    return metadata


def build_audit_event(event_type: str, description: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "description": description,
        "details": details or {},
    }


def build_company_summary(extraction: Dict[str, Any], profile: Dict[str, Any]) -> List[str]:
    """Build 5-10 bullet points for company summary."""
    bullets = []
    if extraction.get("company_name", {}).get("value"):
        bullets.append(f"Legal name: {extraction['company_name']['value']}")
    if profile.get("type"):
        bullets.append(f"Company type: {profile['type']}")
    if extraction.get("turnover_gbp", {}).get("value"):
        bullets.append(f"Revenue: {extraction['turnover_gbp']['value']}")
    if extraction.get("employees", {}).get("value"):
        bullets.append(f"Employees: {extraction['employees']['value']}")
    if extraction.get("industry", {}).get("value"):
        bullets.append(f"Sector: {extraction['industry']['value']}")
    if extraction.get("business_model", {}).get("value"):
        bullets.append(f"Business model: {extraction['business_model']['value']}")
    if extraction.get("geos", {}).get("value"):
        bullets.append(f"Geographies: {extraction['geos']['value']}")
    if extraction.get("fx_intensity", {}).get("value"):
        bullets.append(f"FX profile: {extraction['fx_intensity']['value']}")
    if extraction.get("rarer_insights"):
        bullets.append(f"Key insights: {len(extraction['rarer_insights'])} rarer insights identified")
    return bullets[:10]


def build_pain_points(extraction: Dict[str, Any]) -> Dict[str, List[str]]:
    """Build pain points grouped by category."""
    pains = {
        "payments_acquiring": [],
        "banking_cash_management": [],
        "fx_international": [],
        "spend_management_cards": [],
        "travel": [],
        "lending_working_capital": [],
    }

    # Payments & acquiring
    if extraction.get("payments_acceptance", {}).get("value"):
        pains["payments_acquiring"].append(f"Payment acceptance: {extraction['payments_acceptance']['value']}")
    if extraction.get("providers"):
        provider_names = [p["provider"] for p in extraction["providers"] if p.get("category") == "psp"]
        if provider_names:
            pains["payments_acquiring"].append(f"PSP providers detected: {', '.join(provider_names)}")

    # Banking & cash management
    if extraction.get("spend_profile", {}).get("value"):
        pains["banking_cash_management"].append(f"Spend profile: {extraction['spend_profile']['value']}")

    # FX & international
    if extraction.get("fx_intensity", {}).get("value"):
        pains["fx_international"].append(f"FX intensity: {extraction['fx_intensity']['value']}")
    if extraction.get("geos", {}).get("value") and "international" in extraction["geos"]["value"].lower():
        pains["fx_international"].append(f"International operations: {extraction['geos']['value']}")

    # Spend management & cards
    if extraction.get("ap_payroll_complexity", {}).get("value"):
        pains["spend_management_cards"].append(f"Payroll complexity: {extraction['ap_payroll_complexity']['value']}")

    # Travel - if applicable
    # Lending - if applicable

    return {k: v for k, v in pains.items() if v}


def build_revolut_opportunity(scoring: Dict[str, Any], extraction: Dict[str, Any]) -> Dict[str, Any]:
    """Build Revolut Business opportunity section."""
    pitch = f"This {extraction.get('industry', {}).get('value', 'company')} shows strong fit for Revolut Business with a score of {scoring.get('score', 0)}/100, indicating {scoring.get('priority_tier', 'tier_3')} priority."

    use_cases = []
    score = scoring.get("score", 0)
    if score >= 70:
        use_cases.append({
            "product": "Merchant acquiring + Pay with Revolut + Open Banking",
            "fit": "High digital revenue and payment complexity",
            "priority": "High",
        })
        use_cases.append({
            "product": "FX & multi-currency accounts",
            "fit": "International operations and FX exposure",
            "priority": "High",
        })
        use_cases.append({
            "product": "Cards & spend management",
            "fit": "Complex spend and payroll needs",
            "priority": "High",
        })
    elif score >= 50:
        use_cases.append({
            "product": "FX Forwards",
            "fit": "Predictable FX cashflows",
            "priority": "Medium",
        })
        use_cases.append({
            "product": "Virtual cards",
            "fit": "Supplier and SaaS spend control",
            "priority": "Medium",
        })
    else:
        use_cases.append({
            "product": "Core business banking",
            "fit": "Basic banking and payments",
            "priority": "Low",
        })

    return {
        "pitch_summary": pitch,
        "recommended_use_cases": use_cases[:7],
    }


def build_prospect_report(
    company_number: str,
    company_name: str,
    profile: Dict[str, Any],
    documents: List[Dict[str, Any]],
    extraction: Optional[Dict[str, Any]],
    scoring: Optional[Dict[str, Any]],
    extraction_error: Optional[str] = None,
) -> Dict[str, Any]:
    report_id = f"prospect_{company_number}_{uuid4().hex[:8]}"
    report = {
        "report_id": report_id,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "company_number": company_number,
        "company_name": company_name,
        "company_url": build_company_url(company_number),
        "profile": summarize_profile(profile),
        "documents": [extract_document_metadata(doc) for doc in documents],
        "extraction": extraction,
        "scoring": scoring,
        "summary": {
            "fit_score": scoring.get("score") if scoring else None,
            "priority_tier": scoring.get("priority_tier") if scoring else None,
            "confidence": scoring.get("confidence") if scoring else None,
            "summary_text": scoring.get("summary") if scoring else None,
        },
        "audit_trail": [],
        "status": "success" if not extraction_error else "partial",
        "errors": [],
    }

    # Add analysis sections if extraction available
    if extraction:
        report["company_summary"] = build_company_summary(extraction, profile)
        report["pain_points"] = build_pain_points(extraction)
        report["revolut_opportunity"] = build_revolut_opportunity(scoring or {}, extraction)

    report["audit_trail"].append(
        build_audit_event(
            "company_profile_collected",
            "Company profile successfully collected from Companies House.",
            {"company_number": company_number},
        )
    )

    report["audit_trail"].append(
        build_audit_event(
            "documents_collected",
            f"Collected {len(documents)} relevant documents.",
            {"document_count": len(documents)},
        )
    )

    if extraction_error:
        report["errors"].append({"type": "extraction_error", "message": extraction_error})
        report["audit_trail"].append(
            build_audit_event(
                "extraction_failed",
                "Structured extraction failed.",
                {"error": extraction_error},
            )
        )
    elif extraction is not None:
        report["audit_trail"].append(
            build_audit_event(
                "extraction_completed",
                "Structured schema extraction completed successfully.",
                {"fields_extracted": list(extraction.keys())},
            )
        )

    if scoring is not None:
        report["audit_trail"].append(
            build_audit_event(
                "scoring_completed",
                "Deterministic scoring completed successfully.",
                {"score": scoring.get("score"), "priority_tier": scoring.get("priority_tier")},
            )
        )

    if extraction_error:
        report["status"] = "partial"
    elif extraction is None or scoring is None:
        report["status"] = "incomplete"

    return report
