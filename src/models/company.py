from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class Company(BaseModel):
    company_number: str
    company_name: str
    company_status: Optional[str] = None
    incorporation_date: Optional[date] = None
    registered_address: Optional[str] = None
    headquarters_hypothesis: Optional[str] = None
    sic_codes: List[str] = Field(default_factory=list)
    industry_classification: Optional[str] = None
    business_model_classification: Optional[str] = None
    ownership_type: Optional[str] = None
    parent_company: Optional[str] = None
    group_member_flag: bool = False
    countries_of_operation: List[str] = Field(default_factory=list)
    employee_count: Optional[int] = None
    linkedin_employee_count: Optional[int] = None
    number_of_subsidiaries: Optional[int] = None
    international_subsidiaries: Optional[int] = None
