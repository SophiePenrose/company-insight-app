import base64
from typing import Any, Dict, Optional

import requests


class CompaniesHouseClient:
    api_call_count = 0

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

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 5) -> Dict[str, Any]:
        import time
        delay = 1
        CompaniesHouseClient.api_call_count += 1
        print(f"[CompaniesHouseClient] API call #{CompaniesHouseClient.api_call_count}: {path}")
        for attempt in range(max_retries):
            response = self.session.get(f"{self.base_url}{path}", params=params or {}, timeout=30)
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay = min(delay * 2, 30)  # Exponential backoff, max 30s
                    continue
                else:
                    response.raise_for_status()
            response.raise_for_status()
            return response.json()
        # Should not reach here
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

    def _get_bytes(self, url: str, params: Optional[Dict[str, Any]] = None) -> bytes:
        # Use api_key header for Document API, else use session (Basic Auth)
        if url.startswith("https://document-api.company-information.service.gov.uk"):
            api_key = os.getenv("COMPANIES_HOUSE_API_KEY")
            headers = {"api_key": api_key}
            response = requests.get(url, params=params or {}, headers=headers, timeout=60)
        else:
            response = self.session.get(url, params=params or {}, timeout=60)
        response.raise_for_status()
        return response.content

    def document_content(self, document_path_or_id: str) -> bytes:
        if document_path_or_id.startswith("/"):
            if document_path_or_id.startswith("/document/"):
                url = f"https://document-api.company-information.service.gov.uk{document_path_or_id}"
            else:
                url = f"{self.base_url}{document_path_or_id}"
        elif document_path_or_id.startswith("http"):
            url = document_path_or_id
        else:
            url = f"https://document-api.company-information.service.gov.uk/document/{document_path_or_id}/content"

        return self._get_bytes(url)

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
