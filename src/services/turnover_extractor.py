
Generated Code
from pathlib import Path
text = '''from __future__ import annotations

from typing import Any, Dict, Optional

import requests


class TurnoverExtractor:
    def __init__(self, ch_client=None, timeout: int = 30):
        self.ch_client = ch_client
        self.timeout = timeout

    def get_latest_accounts_filing(self, company_number: str) -> Optional[Dict[str, Any]]:
        if not self.ch_client:
            return None
        filings = self.ch_client.filing_history(company_number)
        items = filings.get("items", [])
        for item in items:
            desc = str(item.get("description", "")).lower()
            if "accounts" in desc:
                return item
        return None

    def get_document_metadata_url(self, filing: Dict[str, Any]) -> Optional[str]:
        links = filing.get("links") or {}
        return links.get("document_metadata") or links.get("document")

    def fetch_document_metadata(self, metadata_url: str) -> Dict[str, Any]:
        if not metadata_url:
            return {}
        try:
            r = requests.get(metadata_url, timeout=self.timeout)
            r.raise_for_status()
            if "json" in r.headers.get("content-type", "").lower():
                return r.json()
            return {"raw": r.text}
        except Exception as e:
            return {"error": str(e)}

    def extract_turnover(self, company_number: str) -> Dict[str, Any]:
        filing = self.get_latest_accounts_filing(company_number)
        if not filing:
            return {"turnover_gbp": None, "source": "no_accounts_filing"}

        metadata_url = self.get_document_metadata_url(filing)
        if not metadata_url:
            return {"turnover_gbp": None, "source": "no_document_metadata"}

        metadata = self.fetch_document_metadata(metadata_url)
        if not metadata or metadata.get("error"):
            return {"turnover_gbp": None, "source": "metadata_error", "error": metadata.get("error")}

        for key in ["turnover", "revenue", "sales"]:
            value = self._deep_find_number(metadata, key)
            if value is not None:
                return {
                    "turnover_gbp": value,
                    "source": f"metadata_{key}",
                    "filing_id": filing.get("transaction_id") or filing.get("id"),
                }

        return {
            "turnover_gbp": None,
            "source": "turnover_not_found",
            "filing_id": filing.get("transaction_id") or filing.get("id"),
            "metadata": metadata,
        }

    def _deep_find_number(self, obj: Any, key_hint: str) -> Optional[float]:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if key_hint in str(k).lower():
                    n = self._coerce_number(v)
                    if n is not None:
                        return n
                n = self._deep_find_number(v, key_hint)
                if n is not None:
                    return n
        elif isinstance(obj, list):
            for item in obj:
                n = self._deep_find_number(item, key_hint)
                if n is not None:
                    return n
        elif isinstance(obj, str):
            if key_hint in obj.lower():
                return self._coerce_number(obj)
        return None

    def _coerce_number(self, value: Any) -> Optional[float]:
        if isinstance(value, (int, float)):
            return float(value)
        if not isinstance(value, str):
            return None
        cleaned = value.replace(",", "").replace("£", "").strip()
        try:
            return float(cleaned)
        except Exception:
            return None
'''
Path('output').mkdir(exist_ok=True)
Path('output/turnover_extractor.py').write_text(text)
print('rewrote output/turnover_extractor.py')
