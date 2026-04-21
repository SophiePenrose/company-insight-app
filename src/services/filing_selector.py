from datetime import datetime
from typing import Any, Dict, List, Optional


class FilingSelector:
    def __init__(self, turnover_extractor):
        self.turnover_extractor = turnover_extractor

    def _parse_date(self, date_str: str):
        return datetime.fromisoformat(date_str).date()

    def select_latest_qualifying(self, candidate_filings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        ordered = sorted(
            candidate_filings,
            key=lambda x: (self._parse_date(x["filing_date"]), -int(x["filing_type_rank"])),
            reverse=True,
        )

        for filing in ordered:
            extracted = self.turnover_extractor.extract(filing)
            if extracted and extracted.get("turnover_gbp") is not None:
                filing.update(extracted)
                return filing

        return None
