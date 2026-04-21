from datetime import date
from typing import Optional

from pydantic import BaseModel


class AccountsFiling(BaseModel):
    filing_id: str
    filing_date: date
    filing_description: str
    filing_type_rank: int
    qualifies_for_turnover_gate: bool
    turnover_gbp: Optional[float] = None
    profit_loss_gbp: Optional[float] = None
    cash_balance_gbp: Optional[float] = None
    debt_position_gbp: Optional[float] = None
    is_group_accounts: bool = False
    source_document_url: Optional[str] = None
    source_section: Optional[str] = None
    extraction_confidence: str = "low"
