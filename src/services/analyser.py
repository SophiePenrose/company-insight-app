from datetime import date
from typing import Any, Dict, List, Optional, Set

from src.models.company import Company
from src.models.filing import AccountsFiling
from src.models.prospect import (
    ProspectRecord,
    UseCaseScore,
    StakeholderCandidate,
)
from src.services.filing_matcher import FilingMatcher
from src.services.filing_selector import FilingSelector
from src.services.provider_detector import ProviderDetector
from src.services.stakeholder_mapper import StakeholderMapper
from src.services.turnover_extractor import TurnoverExtractor


ALLOWED_COMPANY_TYPES: Set[str] = {
    "private limited company",
    "public limited company",
    "limited liability partnership",
    "limited partnership",
    "partnership",
}


class CompanyAnalyser:
    def __init__(self, ch_client, matcher_config: Dict[str, Any]):
        self.ch_client = ch_client
        self.matcher = FilingMatcher(matcher_config)
        self.provider_detector = ProviderDetector()
        self.stakeholder_mapper = StakeholderMapper()
        self.turnover_extractor = TurnoverExtractor(document_fetcher=self)
        self.filing_selector = FilingSelector(turnover_extractor=self.turnover_extractor)

    def fetch_text(self, filing: Dict[str, Any]) -> str:
        text = filing.get("description", "")
        if isinstance(text, str):
            return text
        return str(text)

    def is_eligible_company(self, profile: Dict[str, Any]) -> bool:
        status = str(profile.get("company_status", "")).strip().lower()
        company_type = str(profile.get("type", "")).strip().lower()
        return status == "active" and company_type in ALLOWED_COMPANY_TYPES

    def analyse_company(self, company_number: str) -> Dict[str, Any]:
        profile = self.ch_client.company_profile(company_number)

        if not self.is_eligible_company(profile):
            return {
                "company_number": company_number,
                "eligible": False,
                "eligibility_reason": "Company is not active or company type is not allowed",
            }

        filings = self.ch_client.filing_history(company_number)
        officers = self.ch_client.officers(company_number)

        company = Company(
            company_number=profile.get("company_number", company_number),
            company_name=profile.get("company_name", ""),
            company_status=profile.get("company_status"),
            incorporation_date=self._parse_date(profile.get("date_of_creation")),
            registered_address=self._format_address(profile.get("registered_office_address")),
            sic_codes=profile.get("sic_codes", []),
            parent_company=self._parent_company_name(profile),
            group_member_flag=bool(profile.get("branch_company_details")),
        )

        filing_items = filings.get("items", [])
        matched_filings = self.matcher.matchmany(filing_items, company_number=company_number)
        latest_accounts = self._build_latest_accounts(matched_filings)

        stakeholders = self.stakeholder_mapper.map_officers(officers)

        provider_result = self.provider_detector.detect_from_text(
            " ".join([
                profile.get("company_name", ""),
                " ".join(profile.get("sic_codes", [])),
                profile.get("company_status", ""),
                profile.get("type", ""),
            ])
        )

        eligible = (
            latest_accounts is not None
            and latest_accounts.turnover_gbp is not None
            and latest_accounts.turnover_gbp >= 15000000
        )

        eligibility_reason = (
            "Meets turnover gate"
            if eligible
            else "No qualifying accounts over threshold"
        )

        use_case_scores = self._build_use_case_scores(
            company=company,
            latest_accounts=latest_accounts,
            provider_result=provider_result,
            stakeholders=stakeholders,
        )

        overall_score = max([u.score for u in use_case_scores], default=0)
        priority_tier = self._tier_from_score(overall_score)

        prospect = ProspectRecord(
            company=company,
            eligible=eligible,
            eligibility_reason=eligibility_reason,
            latest_accounts=latest_accounts,
            overall_score=overall_score,
            priority_tier=priority_tier,
            primary_use_case=use_case_scores[0].use_case_name if use_case_scores else None,
            secondary_use_cases=[u.use_case_name for u in use_case_scores[1:3]],
            use_case_scores=use_case_scores,
            signals=[],
            providers=[],
            stakeholders=self._convert_stakeholders(stakeholders),
            pains=[],
            evidence=[],
            recommended_angle=self._recommended_angle(provider_result, stakeholders),
            report_summary=self._summary(company, latest_accounts, overall_score),
        )

        return prospect.model_dump()

    def _build_latest_accounts(self, matched_filings: List[Dict[str, Any]]) -> Optional[AccountsFiling]:
        if not matched_filings:
            return None

        filing = matched_filings[0]
        extracted = self.turnover_extractor.extract(filing) or {}

        filing_date = self._parse_date(filing.get("filing_date"))

        return AccountsFiling(
            filing_id=filing.get("filing_id", ""),
            filing_date=filing_date or date.today(),
            filing_description=filing.get("filing_description", ""),
            filing_type_rank=filing.get("filing_type_rank", 999),
            qualifies_for_turnover_gate=filing.get("qualifies_for_turnover_gate", False),
            turnover_gbp=extracted.get("turnover_gbp"),
            is_group_accounts=filing.get("is_group_accounts", False),
            source_document_url=filing.get("links", {}).get("document_metadata"),
            source_section=extracted.get("source_section"),
            extraction_confidence=extracted.get("extraction_confidence", "low"),
        )

    def _build_use_case_scores(
        self,
        company: Company,
        latest_accounts: Optional[AccountsFiling],
        provider_result: Dict[str, Any],
        stakeholders: List[Dict[str, Any]],
    ) -> List[UseCaseScore]:
        turnover = latest_accounts.turnover_gbp if latest_accounts else 0
        provider_active = provider_result.get("is_provider_active", False)
        stakeholder_score = max([s.get("seniority_score", 0) for s in stakeholders], default=0)

        scores = [
            UseCaseScore(
                use_case_name="treasury",
                score=min(
                    100,
                    (20 if turnover and turnover >= 15000000 else 0)
                    + (20 if provider_active else 0)
                    + (10 if stakeholder_score >= 80 else 0),
                ),
                confidence="medium",
                reason="Potential treasury workflow fit",
                evidence_ids=[],
            ),
            UseCaseScore(
                use_case_name="payments",
                score=min(
                    100,
                    (15 if provider_active else 0)
                    + (15 if stakeholder_score >= 75 else 0),
                ),
                confidence="medium",
                reason="Potential payments workflow fit",
                evidence_ids=[],
            ),
            UseCaseScore(
                use_case_name="expense_cards",
                score=min(
                    100,
                    (10 if turnover and turnover >= 20000000 else 0)
                    + (10 if stakeholder_score >= 70 else 0),
                ),
                confidence="low",
                reason="Possible card/expense workflow fit",
                evidence_ids=[],
            ),
        ]
        return sorted(scores, key=lambda x: x.score, reverse=True)

    def _convert_stakeholders(self, stakeholders: List[Dict[str, Any]]) -> List[StakeholderCandidate]:
        result = []
        for s in stakeholders:
            result.append(
                StakeholderCandidate(
                    name=s.get("name", ""),
                    title=s.get("title", ""),
                    stakeholder_category=s.get("stakeholder_category", ""),
                    seniority_score=s.get("seniority_score", 0),
                    decision_relevance=s.get("decision_relevance", "medium"),
                    source_type=s.get("source_type", "companies_house_officers"),
                    source_title=s.get("source_title", ""),
                    source_url=s.get("source_url"),
                    is_current=s.get("is_current", True),
                    confidence=s.get("confidence", "medium"),
                    why_relevant=s.get("why_relevant"),
                    evidence_ids=s.get("evidence_ids", []),
                )
            )
        return result

    def _recommended_angle(self, provider_result: Dict[str, Any], stakeholders: List[Dict[str, Any]]) -> str:
        if provider_result.get("is_provider_active"):
            return f"Lead with {provider_result.get('primary_provider', 'current provider')} replacement or complement angle."
        if stakeholders:
            return "Lead with finance operations and treasury efficiency angle."
        return "Lead with a general finance efficiency angle."

    def _summary(self, company: Company, latest_accounts: Optional[AccountsFiling], overall_score: float) -> str:
        turnover = latest_accounts.turnover_gbp if latest_accounts and latest_accounts.turnover_gbp else None
        if turnover:
            return f"{company.company_name} scored {overall_score:.0f}. Turnover: £{turnover:,.0f}"
        return f"{company.company_name} scored {overall_score:.0f}."

    def _format_address(self, addr: Optional[Dict[str, Any]]) -> Optional[str]:
        if not addr:
            return None
        parts = [
            addr.get("address_line_1"),
            addr.get("address_line_2"),
            addr.get("locality"),
            addr.get("postal_code"),
            addr.get("country"),
        ]
        return ", ".join([p for p in parts if p])

    def _parent_company_name(self, profile: Dict[str, Any]) -> Optional[str]:
        details = profile.get("branch_company_details") or {}
        return details.get("parent_company_name")

    def _tier_from_score(self, score: float) -> str:
        if score >= 80:
            return "A"
        if score >= 60:
            return "B"
        if score >= 40:
            return "C"
        return "D"

    def _parse_date(self, value: Any) -> Optional[date]:
        if not value:
            return None
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value))
        except Exception:
            return None
