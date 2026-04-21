import re
from typing import Any, Dict, List, Optional


class FilingMatcher:
    def __init__(self, matcher_config: Dict[str, Any]):
        self.patterns = matcher_config.get("accepted_accounts_patterns", [])

    def _normalize_text(self, filing_item: Dict[str, Any]) -> str:
        parts = [str(filing_item.get("description", ""))]
        description_values = filing_item.get("description_values", {})
        if isinstance(description_values, dict):
            parts.extend([str(v) for v in description_values.values()])
        else:
            parts.append(str(description_values))
        return " ".join(parts).lower()

    def match(self, filing_item: Dict[str, Any], company_number: Optional[str] = None) -> Optional[Dict[str, Any]]:
        text = self._normalize_text(filing_item)

        for pattern in self.patterns:
            if re.search(pattern["regex"], text, re.I):
                links = filing_item.get("links", {}) or {}
                return {
                    "filing_id": filing_item.get("transaction_id")
                    or filing_item.get("barcode")
                    or filing_item.get("id")
                    or "unknown",
                    "company_number": company_number,
                    "filing_date": filing_item.get("date"),
                    "filing_description": filing_item.get("description", ""),
                    "filing_type_rank": pattern["rank"],
                    "qualifies_for_turnover_gate": pattern["qualifies_for_turnover_gate"],
                    "is_group_accounts": pattern["is_group_accounts"],
                    "category": filing_item.get("category"),
                    "barcode": filing_item.get("barcode"),
                    "description_values": filing_item.get("description_values", {}),
                    "links": links,
                }
        return None

    def match_many(self, filings: List[Dict[str, Any]], company_number: Optional[str] = None) -> List[Dict[str, Any]]:
        matches = []
        for item in filings:
            matched = self.match(item, company_number=company_number)
            if matched:
                matches.append(matched)
        return matches
