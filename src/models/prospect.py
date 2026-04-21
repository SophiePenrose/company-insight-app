from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from .company import Company
from .filing import AccountsFiling


class UseCaseScore(BaseModel):
    use_case_name: str
    score: float
    confidence: str
    reason: str
    evidence_ids: List[str] = Field(default_factory=list)


class Signal(BaseModel):
    signal_id: str
    signal_name: str
    category: str
    source_type: str
    source_title: str
    source_date: str
    excerpt: str
    trigger_reason: str
    confidence: str
    freshness_weight: float = 1.0


class ProviderMention(BaseModel):
    provider_name: str
    category: str
    status: str
    evidence_ids: List[str] = Field(default_factory=list)


class StakeholderCandidate(BaseModel):
    name: str
    title: str
    stakeholder_category: str
    seniority_score: float
    decision_relevance: str
    source_type: str
    source_title: str
    source_url: Optional[str] = None
    is_current: bool = True
    confidence: str = "medium"
    why_relevant: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)


class PainInference(BaseModel):
    pain_name: str
    kind: str
    confidence: str
    evidence_ids: List[str] = Field(default_factory=list)


class Evidence(BaseModel):
    evidence_id: str
    source_type: str
    source_title: str
    source_date: str
    section_name: Optional[str] = None
    excerpt: str
    why_it_matters: Optional[str] = None
    confidence: str = "medium"


class ProspectRecord(BaseModel):
    company: Company
    eligible: bool
    eligibility_reason: str
    latest_accounts: Optional[AccountsFiling] = None
    overall_score: float = 0
    priority_tier: str = "D"
    primary_use_case: Optional[str] = None
    secondary_use_cases: List[str] = Field(default_factory=list)
    use_case_scores: List[UseCaseScore] = Field(default_factory=list)
    signals: List[Signal] = Field(default_factory=list)
    providers: List[ProviderMention] = Field(default_factory=list)
    stakeholders: List[StakeholderCandidate] = Field(default_factory=list)
    pains: List[PainInference] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    recommended_angle: Optional[str] = None
    report_summary: Optional[str] = None

    @model_validator(mode="after")
    def validate_eligibility(self):
        if self.eligible:
            if not self.latest_accounts:
                raise ValueError("Eligible records must include latest_accounts")
            if self.latest_accounts.turnover_gbp is None or self.latest_accounts.turnover_gbp < 15000000:
                raise ValueError("Eligible records must have turnover >= 15000000")
        return self
