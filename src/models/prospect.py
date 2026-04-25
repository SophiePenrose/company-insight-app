from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Company(BaseModel):
    """Core company entity with all baseline data."""
    # Identity
    company_number: str
    company_name: str
    legal_entity_type: str  # 'private limited', 'public limited', 'llp', etc.
    status: str  # 'active', 'dissolved', etc.

    # Location & Structure
    registered_address: str
    hq_address: Optional[str] = None
    incorporation_date: date
    countries_of_operation: List[str]

    # Financials
    latest_revenue_gbp: Optional[float] = None
    revenue_growth_pct: Optional[float] = None
    profitability: Optional[float] = None
    cash_balance_gbp: Optional[float] = None
    debt_gbp: Optional[float] = None
    employee_count: Optional[int] = None
    linkedin_employee_count: Optional[int] = None

    # Structure
    parent_company_number: Optional[str] = None
    number_of_subsidiaries: int
    international_subsidiary_count: int
    ownership_type: str  # 'private', 'public', 'private equity', 'family', etc.

    # Classification
    sic_codes: List[str]
    industry_classification: str
    business_model: str  # 'ecommerce', 'saas', 'marketplace', 'importer', etc.

    # Pipeline metadata
    data_collection_date: datetime
    freshness_score: float  # 0-100, reflects recency of data
    confidence_score: float  # 0-100, reflects data quality


class Filing(BaseModel):
    """Filing entity with extracted text sections."""
    filing_id: str
    company_number: str
    filing_type: str  # 'annual accounts', 'strategic report', etc.
    filing_date: date
    filing_url: Optional[str]

    # Extracted text sections
    sections: Dict[str, str] = Field(default_factory=dict)

    extracted_at: datetime
    source: str  # 'companies_house', 'news', 'linkedin', etc.


class Signal(BaseModel):
    """Detected signal with evidence."""
    signal_id: str
    company_number: str
    signal_type: str  # 'fx_exposure', 'international_subsidiaries', etc.
    signal_category: str  # 'cross_border', 'growth', 'finance_transformation', etc.

    # Evidence
    evidence_text: str  # Direct excerpt
    source_type: str  # 'filing', 'news', 'linkedin', 'web'
    source_title: str
    source_date: date
    source_url: Optional[str]

    # Metadata
    detected_at: datetime
    confidence: str  # 'high', 'medium', 'low'
    is_inferred: bool  # True if inferred from signals, False if directly evidenced
    recency_decay_factor: float  # 1.0 for fresh, decays for older signals

    # Use case relevance
    relevant_use_cases: List[str]  # Which use cases this signal impacts
    weight_multiplier: float  # How heavily this signal should be weighted


class ProviderUsage(BaseModel):
    """Detected provider/competitor usage."""
    provider_name: str  # 'Stripe', 'Wise', etc.
    provider_category: str  # 'payment_processor', 'fx_provider', 'business_bank', etc.

    # Confidence levels
    confidence: str  # 'confirmed', 'likely', 'possible', 'stale'
    evidence_count: int  # How many sources mention this provider

    # Evidence
    evidence_texts: List[Dict] = Field(default_factory=list)

    last_mentioned: date
    is_active_mention: bool  # True if mentioned recently as current usage


class UseCaseScore(BaseModel):
    """Score for a specific use case."""
    use_case_name: str  # One of 8 predefined use cases
    company_number: str

    # Scoring
    overall_score: float  # 0-100
    confidence_level: str  # 'high', 'medium', 'low'

    # Breakdown by signal category
    signal_scores: Dict[str, float] = Field(default_factory=dict)

    # Evidence
    top_contributing_signals: List[str]  # Signal IDs
    recommended_emphasis: str  # Sales angle for this use case


class InferredPain(BaseModel):
    """Inferred pain point from signals."""
    pain_type: str  # 'fx_cost_leakage', 'reconciliation_burden', etc.
    company_number: str
    confidence: str  # 'high', 'medium', 'low'

    # Evidence
    inferred_from_signals: List[str]  # Signal IDs supporting this pain
    evidence_summary: str

    # Is this pain directly evidenced or inferred?
    is_directly_evidenced: bool


class ProspectReport(BaseModel):
    """Complete prospect report."""
    report_id: str
    company_number: str
    generated_at: datetime

    # Overall assessment
    overall_readiness_score: float  # 0-100
    confidence_level: str  # 'high', 'medium', 'low'
    priority_tier: str  # 'tier_1', 'tier_2', 'tier_3'
    summary_assessment: str

    # Company snapshot
    company_overview: Company

    # Use case analysis
    primary_use_case: Optional[UseCaseScore] = None
    secondary_use_cases: List[UseCaseScore] = Field(default_factory=list)
    all_use_case_scores: Dict[str, float] = Field(default_factory=dict)

    # Signals & detection
    detected_signals: List[Signal] = Field(default_factory=list)
    trigger_events: List[Signal] = Field(default_factory=list)
    provider_usage: List[ProviderUsage] = Field(default_factory=list)

    # Pains
    evidenced_pains: List[InferredPain] = Field(default_factory=list)
    inferred_pains: List[InferredPain] = Field(default_factory=list)

    # Recommended action
    recommended_outreach_angle: str
    suggested_entry_point: str  # Which product to lead with

    # Evidence audit trail
    signal_summary: Dict[str, int] = Field(default_factory=dict)
    data_freshness: Dict[str, date] = Field(default_factory=dict)
