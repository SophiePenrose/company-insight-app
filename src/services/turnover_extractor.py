import re
from typing import Any, Dict, Optional


TURNOVER_PATTERNS = [
    r"turnover[^0-9£]{0,80}£?\s?([\d,]+(?:\.\d+)?)",
    r"revenue[^0-9£]{0,80}£?\s?([\d,]+(?:\.\d+)?)",
    r"group turnover[^0-9£]{0,80}£?\s?([\d,]+(?:\.\d+)?)",
    r"gross operating revenue[^0-9£]{0,80}£?\s?([\d,]+(?:\.\d+)?)",
]


class TurnoverExtractor:
    def __init__(self, document_fetcher):
        self.document_fetcher = document_fetcher

    def _parse_amount(self, value: str) -> Optional[float]:
        try:
            cleaned = value.replace(",", "").strip()
            return float(cleaned)
        except Exception:
            return None

    def extract(self, filing: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        text = self.document_fetcher.fetch_text(filing)
        if not text:
            return None

        for pattern in TURNOVER_PATTERNS:
            match = re.search(pattern, text, re.I)
            if match:
                amount = self._parse_amount(match.group(1))
                if amount is not None:
                    return {
                        "turnover_gbp": amount,
                        "source_section": "turnover/revenue",
                        "extraction_confidence": "medium",
                    }

        return None
