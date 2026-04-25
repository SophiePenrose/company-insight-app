from typing import Literal, Optional, List
from pydantic import BaseModel, Field

Confidence = Literal["high", "medium", "low"]
ProviderCategory = Literal["bank", "psp", "ecom", "erp", "expenses", "payroll_eor", "treasury"]
ProviderDetectedAs = Literal["explicit", "inferred"]
RarerInsightType = Literal["goal", "cost", "risk", "policy", "working_capital"]


class Evidence(BaseModel):
    quote: str
    source: str
    url: Optional[str] = None


class FieldValue(BaseModel):
    value: Optional[str] = None
    confidence: Confidence = "low"
    evidence: List[Evidence] = Field(default_factory=list)


class RarerInsight(BaseModel):
    type: RarerInsightType
    insight: str
    strength_1_to_5: int
    evidence: Evidence


class ProviderDetection(BaseModel):
    provider: str
    category: ProviderCategory
    detected_as: ProviderDetectedAs
    confidence: Confidence
    evidence: List[Evidence] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    company_name: FieldValue
    turnover_gbp: FieldValue
    employees: FieldValue
    industry: FieldValue
    business_model: FieldValue
    geos: FieldValue
    fx_intensity: FieldValue
    payments_acceptance: FieldValue
    spend_profile: FieldValue
    ap_payroll_complexity: FieldValue
    tech_stack: FieldValue
    triggers: FieldValue
    rarer_insights: List[RarerInsight] = Field(default_factory=list)
    providers: List[ProviderDetection] = Field(default_factory=list)
