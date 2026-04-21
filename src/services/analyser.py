from datetime import date
from typing import Any, Dict, List, Optional, Set

import requests

from src.models.company import Company
from src.models.filing import AccountsFiling
from src.models.prospect import ProspectRecord, UseCaseScore, StakeholderCandidate
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
    def __init__(self, ch_client, matcher_config: Dict[str, Any], convert_ixbrl_base_url: Optional[str] = None, convert_ixbrl_api_key: Optional[str] = None):
        self.ch_client = ch_client
        self.matcher = FilingMatcher(matcher_config)
        self.provider_detector = ProviderDetector()
        self.stakeholder_mapper = StakeholderMapper()
        self.turnover_extractor = TurnoverExtractor(document_fetcher=self)
        self.filing_selector = FilingSelector(turnover_extractor=self.turnover_extractor)
        self.convert_ixbrl_base_url = convert_ixbrl_base_url or "https://convert-ixbrl.co.uk"
        self.convert_ixbrl_api_key = convert_ixbrl_api_key

    def fetch_text(self, filing: Dict[str, Any]) -> str:
        text = filing.get("description", "")
        if isinstance(text, str):
            return text
        return str(text)

    def is_eligible_company(self, profile: Dict[str, Any]) -> bool:
        status = str(profile.get("company_status", "")).strip().lower()
        company_type = str(profile.get("type", "")).strip().lower()
        return status == "active" and company_type in ALLOWED_COMPANY_TYPES

    def get_financials_metadata(self, company_number: str) -> Dict[str, Any]:
        url = f"
