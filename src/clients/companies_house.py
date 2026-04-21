import base64
from typing import Any, Dict, Optional

import requests


class CompaniesHouseClient:
    def __init__(self, api_key: str, base_url: str = "https://api.company-information.service.gov.uk"):
        if not api_key:
            raise ValueError("Companies House API key is required")

        token = base64.b64encode(f"{api_key}:".encode()).decode()
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Basic {token}",
                "User-Agent": "revolut-prospect-engine",
            }
        )

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = self.session.get(f"{self.base_url}{path}", params=params or {}, timeout=30)
        response.raise_for_status()
        return response.json()

    def search_companies(self, query: str, items_per_page: int = 20, start_index: int = 0) -> Dict[str, Any]:
        return self._get(
            "/search/companies",
            params={
                "q": query,
                "items_per_page": items_per_page,
                "start_index": start_index,
            },
        )

    def company_profile(self, company_number: str) -> Dict[str, Any]:
        return self._get(f"/company/{company_number}")

    def filing_history(self, company_number: str, items_per_page: int = 100, start_index: int = 0) -> Dict[str, Any]:
        return self._get(
            f"/company/{company_number}/filing-history",
            params={
                "items_per_page": items_per_page,
                "start_index": start_index,
            },
        )

    def filing_history_item(self, company_number: str, transaction_id: str) -> Dict[str, Any]:
        return self._get(f"/company/{company_number}/filing-history/{transaction_id}")

    def officers(self, company_number: str, items_per_page: int = 100, start_index: int = 0) -> Dict[str, Any]:
        return self._get(
            f"/company/{company_number}/officers",
            params={
                "items_per_page": items_per_page,
                "start_index": start_index,
            },
        )

    def psc(self, company_number: str, items_per_page: int = 100, start_index: int = 0) -> Dict[str, Any]:
        return self._get(
            f"/company/{company_number}/persons-with-significant-control",
            params={
                "items_per_page": items_per_page,
                "start_index": start_index,
            },
        )
