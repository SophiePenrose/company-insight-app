from typing import Any, Dict, Optional

from src.clients.companies_house import CompaniesHouseClient
from src.services.filing_matcher import FilingMatcher
from src.services.filing_selector import FilingSelector
from src.services.provider_detector import ProviderDetector
from src.services.turnover_extractor import TurnoverExtractor


class DocumentFetcher:
    """Mock document fetcher for extracting text from filings."""

    def __init__(self, ch_client: CompaniesHouseClient):
        self.ch_client = ch_client

    def fetch_text(self, filing: Dict[str, Any]) -> Optional[str]:
        """Extract text from filing (placeholder implementation)."""
        # In a real implementation, this would fetch the actual filing document
        # For now, return the filing description as text
        return filing.get("filing_description", "")


class CompanyAnalyser:
    def __init__(self, ch_client: CompaniesHouseClient, matcher_config: Dict[str, Any]):
        self.ch_client = ch_client
        self.matcher_config = matcher_config or {}

        # Initialize services
        document_fetcher = DocumentFetcher(ch_client)
        self.filing_matcher = FilingMatcher(self.matcher_config)
        self.turnover_extractor = TurnoverExtractor(document_fetcher)
        self.filing_selector = FilingSelector(self.turnover_extractor)
        self.provider_detector = ProviderDetector()

    def analyse_company(self, company_number: str) -> Dict[str, Any]:
        """Analyse a company by fetching profile, filings, and extracting key information."""
        try:
            # Fetch company profile
            profile = self.ch_client.company_profile(company_number)

            # Fetch filing history
            filing_history_data = self.ch_client.filing_history(company_number)
            filings = filing_history_data.get("items", [])

            # Match filings
            matched_filings = self.filing_matcher.match_many(filings, company_number=company_number)

            # Select best qualifying filing
            best_filing = self.filing_selector.select_latest_qualifying(matched_filings) if matched_filings else None

            # Detect payment providers from company info
            provider_detection = self.provider_detector.detect_from_text(
                f"{profile.get('company_name', '')} {profile.get('company_status', '')}"
            )

            # Build result
            result = {
                "company_number": company_number,
                "company_name": profile.get("company_name"),
                "company_status": profile.get("company_status"),
                "incorporation_date": profile.get("date_of_creation"),
                "sic_codes": [sic.get("sic_code") for sic in profile.get("sic_codes", [])],
                "registered_address": self._format_address(profile.get("registered_office_address", {})),
                "employee_count": profile.get("employee_count"),
                "matched_filings_count": len(matched_filings),
                "best_filing": best_filing,
                "provider_detection": provider_detection,
            }

            return result

        except Exception as e:
            return {
                "company_number": company_number,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    def _format_address(self, address: Dict[str, Any]) -> Optional[str]:
        """Format address dictionary into a string."""
        if not address:
            return None
        parts = [
            address.get("address_line_1"),
            address.get("address_line_2"),
            address.get("locality"),
            address.get("postal_code"),
            address.get("country"),
        ]
>>>>>>> badf3c8 (Prepare for cloud deployment: add packages.txt, ensure all code and config included)
