from __future__ import annotations

import re
from typing import Any, Dict, Optional

import requests


TURNOVER_PATTERNS = [
    r"turnover\s*[:\-]?\s*£?([0-9][0-9,\. ]+)",
    r"revenue\s*[:\-]?\s*£?([0-9][0-9,\. ]+)",
    r"sales\s*[:\-]?\s*£?([0-9][0-9,\. ]+)",
]


class TurnoverExtractor:
    def __init__(self, document_fetcher=None, timeout: int = 30):
        self.document_fetcher = document_fetcher
        self.timeout = timeout

    def extract(self, filing: Dict[str, Any]) -> Dict[str, Any]:
        text = self._get_text(filing)
        if not text:
            return {"turnover_gbp": None, "source_section": None, "extraction_confidence": "low"}

        for pattern in TURNOVER_PATTERNS:
            m = re.search(pattern, text, re.I)
            if m:
                value = self._parse_money(m.group(1))
                if value is not None:
                    return {
                        "turnover_gbp": value,
                        "source_section": "text_match",
                        "extraction_confidence": "medium",
                    }

        return {"turnover_gbp": None, "source_section": None, "extraction_confidence": "low"}

    def fetch_document_text(self, document_url: str) -> str:
        if not document_url:
            return ""
        try:
            r = requests.get(document_url, timeout=self.timeout)
            r.raise_for_status()
            return r.text
        except Exception:
            return ""

    def _get_text(self, filing: Dict[str, Any]) -> str:
        candidates = [
            filing.get("full_text"),
            filing.get("description"),
            filing.get("notes"),
            filing.get("document_text"),
        ]
        for c in candidates:
            if isinstance(c, str) and c.strip():
                return c

        links = filing.get("links") or {}
        doc_url = links.get("document_metadata") or links.get("document")
        if doc_url:
            return self.fetch_document_text(doc_ur
