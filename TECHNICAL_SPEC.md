# Technical Build Spec: UK Mid-Market Prospect Readiness Engine for Revolut Business

## 1. Data Model / Entities

### 1.1 Core Company Entity

```python
class Company(BaseModel):
    # Identity
    company_number: str
    company_name: str
    legal_entity_type: str  # 'private limited', 'public limited', 'llp', etc.
    status: str  # 'active', 'dissolved', etc.
    
    # Location & Structure
    registered_address: str
    hq_address: Optional[str]
    incorporation_date: date
    countries_of_operation: List[str]
    
    # Financials
    latest_revenue_gbp: Optional[float]
    revenue_growth_pct: Optional[float]
    profitability: Optional[float]
    cash_balance_gbp: Optional[float]
    debt_gbp: Optional[float]
    employee_count: Optional[int]
    linkedin_employee_count: Optional[int]
    
    # Structure
    parent_company_number: Optional[str]
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
```

### 1.2 Filing Entity

```python
class Filing(BaseModel):
    filing_id: str
    company_number: str
    filing_type: str  # 'annual accounts', 'strategic report', etc.
    filing_date: date
    filing_url: Optional[str]
    
    # Extracted text sections
    sections: Dict[str, str] = {
        "strategic_report": "",
        "principal_risks": "",
        "directors_report": "",
        "notes_to_accounts": "",
        "group_overview": ""
    }
    
    extracted_at: datetime
    source: str  # 'companies_house', 'news', 'linkedin', etc.
```

### 1.3 Signal Entity

```python
class Signal(BaseModel):
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
```

### 1.4 Provider Detection Entity

```python
class ProviderUsage(BaseModel):
    provider_name: str  # 'Stripe', 'Wise', etc.
    provider_category: str  # 'payment_processor', 'fx_provider', 'business_bank', etc.
    
    # Confidence levels
    confidence: str  # 'confirmed', 'likely', 'possible', 'stale'
    evidence_count: int  # How many sources mention this provider
    
    # Evidence
    evidence_texts: List[Dict] = [
        {
            "text": "...",
            "source_type": "filing|news|linkedin|web",
            "source_date": "date",
            "confidence": "high|medium|low"
        }
    ]
    
    last_mentioned: date
    is_active_mention: bool  # True if mentioned recently as current usage
```

### 1.5 Use Case Score Entity

```python
class UseCaseScore(BaseModel):
    use_case_name: str  # One of 8 predefined use cases
    company_number: str
    
    # Scoring
    overall_score: float  # 0-100
    confidence_level: str  # 'high', 'medium', 'low'
    
    # Breakdown by signal category
    signal_scores: Dict[str, float] = {
        "cross_border_signals": 0.0,
        "growth_signals": 0.0,
        "finance_transformation_signals": 0.0,
        "provider_complexity_signals": 0.0,
        "pain_signals": 0.0,
        "trigger_events": 0.0
    }
    
    # Evidence
    top_contributing_signals: List[str]  # Signal IDs
    recommended_emphasis: str  # Sales angle for this use case
```

### 1.6 Pain Inference Entity

```python
class InferredPain(BaseModel):
    pain_type: str  # 'fx_cost_leakage', 'reconciliation_burden', etc.
    company_number: str
    confidence: str  # 'high', 'medium', 'low'
    
    # Evidence
    inferred_from_signals: List[str]  # Signal IDs supporting this pain
    evidence_summary: str
    
    # Is this pain directly evidenced or inferred?
    is_directly_evidenced: bool
```

### 1.7 Prospect Report Entity

```python
class ProspectReport(BaseModel):
    report_id: str
    company_number: str
    generated_at: datetime
    
    # Overall assessment
    overall_readiness_score: float  # 0-100
    priority_tier: str  # 'tier_1', 'tier_2', 'tier_3'
    summary_assessment: str
    
    # Company snapshot
    company_overview: Company
    
    # Use case analysis
    primary_use_case: UseCaseScore
    secondary_use_cases: List[UseCaseScore]
    all_use_case_scores: Dict[str, float]  # use_case_name -> score
    
    # Signals & detection
    detected_signals: List[Signal]
    provider_usage: List[ProviderUsage]
    trigger_events: List[Signal]  # Recent high-impact signals
    
    # Pains
    evidenced_pains: List[InferredPain]
    inferred_pains: List[InferredPain]
    
    # Recommended action
    recommended_outreach_angle: str
    suggested_entry_point: str  # Which product to lead with
    
    # Evidence audit trail
    signal_summary: Dict[str, int]  # category -> count
    data_freshness: Dict[str, date]  # source_type -> latest_date
```

---

## 2. Signal Schema

All signals conform to this structure:

```python
SIGNAL_DEFINITIONS = {
    "cross_border_signals": [
        {
            "signal_id": "fx_exposure_mentioned",
            "name": "FX Exposure Mentioned",
            "category": "cross_border",
            "keywords": ["foreign exchange", "fx exposure", "currency exposure"],
            "relevant_use_cases": ["fx_international_money", "core_banking"],
            "base_weight": 8.0,
            "evidence_type": "text_extraction",
            "confidence_required": "medium"
        },
        {
            "signal_id": "international_subsidiaries",
            "name": "International Subsidiaries Present",
            "category": "cross_border",
            "detection_logic": "subsidiary_count > 0 AND subsidiary_country != 'UK'",
            "relevant_use_cases": ["fx_international_money", "core_banking"],
            "base_weight": 7.5,
            "evidence_type": "structured_data",
            "confidence_required": "high"
        },
        {
            "signal_id": "overseas_suppliers",
            "name": "Overseas Suppliers Mentioned",
            "category": "cross_border",
            "keywords": ["overseas supplier", "foreign supplier", "imported", "foreign purchase"],
            "relevant_use_cases": ["fx_international_money", "accounting_integration"],
            "base_weight": 7.0,
            "evidence_type": "text_extraction",
            "confidence_required": "medium"
        }
    ],
    
    "growth_signals": [
        {
            "signal_id": "strong_revenue_growth",
            "name": "Strong Revenue Growth",
            "category": "growth",
            "detection_logic": "revenue_growth_pct > 25",
            "relevant_use_cases": ["merchant_acquiring", "core_banking", "cards_spend"],
            "base_weight": 6.0,
            "evidence_type": "structured_data",
            "confidence_required": "high"
        },
        {
            "signal_id": "employee_expansion",
            "name": "Employee Expansion",
            "category": "growth",
            "detection_logic": "employee_growth_rate > 20",
            "relevant_use_cases": ["cards_spend", "core_banking"],
            "base_weight": 5.5,
            "evidence_type": "structured_data",
            "confidence_required": "medium"
        }
    ],
    
    "finance_transformation_signals": [
        {
            "signal_id": "new_finance_leadership",
            "name": "New Finance Leadership",
            "category": "finance_transformation",
            "keywords": ["new cfo", "appointed finance director", "head of treasury"],
            "relevant_use_cases": ["core_banking", "accounting_integration"],
            "base_weight": 8.5,
            "evidence_type": "text_extraction",
            "confidence_required": "high"
        },
        {
            "signal_id": "finance_ops_hiring",
            "name": "Finance/Treasury Hiring",
            "category": "finance_transformation",
            "keywords": ["finance operations", "treasury", "financial controller"],
            "relevant_use_cases": ["core_banking", "accounting_integration"],
            "base_weight": 7.0,
            "evidence_type": "text_extraction",
            "confidence_required": "medium"
        }
    ],
    
    "provider_complexity_signals": [
        {
            "signal_id": "multiple_banks",
            "name": "Multiple Banks Detected",
            "category": "provider_complexity",
            "detection_logic": "provider_usage.filter(category='business_bank').count() > 1",
            "relevant_use_cases": ["core_banking"],
            "base_weight": 7.5,
            "evidence_type": "provider_detection",
            "confidence_required": "medium"
        },
        {
            "signal_id": "fragmented_payment_stack",
            "name": "Fragmented Payment Stack",
            "category": "provider_complexity",
            "detection_logic": "provider_usage.filter(category='payment_processor').count() > 1",
            "relevant_use_cases": ["merchant_acquiring", "core_banking"],
            "base_weight": 8.0,
            "evidence_type": "provider_detection",
            "confidence_required": "medium"
        }
    ],
    
    "pain_signals": [
        {
            "signal_id": "margin_pressure",
            "name": "Margin Pressure",
            "category": "pain",
            "keywords": ["margin pressure", "cost pressure", "rising costs"],
            "relevant_use_cases": ["merchant_acquiring", "fx_international_money"],
            "base_weight": 6.5,
            "evidence_type": "text_extraction",
            "confidence_required": "medium"
        },
        {
            "signal_id": "working_capital_constraint",
            "name": "Working Capital Constraint",
            "category": "pain",
            "keywords": ["working capital", "cash flow", "liquidity"],
            "relevant_use_cases": ["merchant_acquiring", "fx_international_money", "lending"],
            "base_weight": 7.5,
            "evidence_type": "text_extraction",
            "confidence_required": "medium"
        }
    ],
    
    "trigger_events": [
        {
            "signal_id": "funding_round",
            "name": "Recent Funding Round",
            "category": "trigger",
            "keywords": ["funding", "investment", "capital raise"],
            "relevant_use_cases": ["core_banking", "merchant_acquiring"],
            "base_weight": 9.0,
            "evidence_type": "text_extraction",
            "confidence_required": "high"
        },
        {
            "signal_id": "acquisition",
            "name": "Acquisition Event",
            "category": "trigger",
            "keywords": ["acquired", "acquisition", "purchased"],
            "relevant_use_cases": ["core_banking", "fx_international_money"],
            "base_weight": 8.5,
            "evidence_type": "text_extraction",
            "confidence_required": "high"
        }
    ]
}
```

---

## 3. Scoring Objects

### 3.1 Use Case Scoring Logic

```python
class UseCaseScorer:
    """
    Scores each use case 0-100 based on detected signals.
    Returns overall score + breakdown.
    """
    
    USE_CASES = [
        "core_banking",
        "fx_international_money",
        "merchant_acquiring",
        "apis_developer_tooling",
        "cards_spend_management",
        "travel_conferma",
        "accounting_integration",
        "lending_credit"
    ]
    
    # Use-case-specific weights by signal category
    USE_CASE_WEIGHTS = {
        "fx_international_money": {
            "cross_border_signals": 0.40,  # Highest weight
            "growth_signals": 0.10,
            "finance_transformation_signals": 0.05,
            "provider_complexity_signals": 0.10,
            "pain_signals": 0.25,
            "trigger_events": 0.10
        },
        "merchant_acquiring": {
            "cross_border_signals": 0.15,
            "growth_signals": 0.15,
            "finance_transformation_signals": 0.05,
            "provider_complexity_signals": 0.25,
            "pain_signals": 0.25,
            "trigger_events": 0.15
        },
        "core_banking": {
            "cross_border_signals": 0.20,
            "growth_signals": 0.15,
            "finance_transformation_signals": 0.20,
            "provider_complexity_signals": 0.25,
            "pain_signals": 0.15,
            "trigger_events": 0.05
        },
        # ... etc for all 8 use cases
    }
    
    def score_use_case(self, company: Company, signals: List[Signal], 
                       use_case: str) -> UseCaseScore:
        """
        1. Filter signals relevant to this use case
        2. Calculate score by category
        3. Apply use-case-specific weights
        4. Apply recency decay
        5. Return score object with breakdown
        """
        pass
    
    def score_all_use_cases(self, company: Company, signals: List[Signal]) -> Dict[str, float]:
        """
        Score all 8 use cases and return ranked list.
        """
        pass
```

### 3.2 Overall Readiness Scoring Logic

```python
class OverallReadinessScorer:
    """
    Aggregates use-case scores into overall readiness score.
    Applies Revolut-specific weighting.
    """
    
    # Revolut's priority hierarchy for use cases
    USE_CASE_IMPORTANCE = {
        "merchant_acquiring": 1.0,  # Baseline
        "fx_international_money": 1.0,
        "cards_spend_management": 0.9,
        "core_banking": 0.85,
        "accounting_integration": 0.8,
        "apis_developer_tooling": 0.7,
        "travel_conferma": 0.5,
        "lending_credit": 0.6
    }
    
    def score_overall(self, use_case_scores: Dict[str, float]) -> float:
        """
        1. Weight each use case by importance
        2. Apply company-type modifiers
        3. Apply company-size modifiers
        4. Calculate 0-100 score
        5. Assign priority tier (tier_1, tier_2, tier_3)
        """
        pass
    
    def assign_priority_tier(self, overall_score: float) -> str:
        """
        tier_1: 75-100 (immediate outreach)
        tier_2: 50-74 (strong potential, needs context)
        tier_3: 0-49 (weak fit or incomplete data)
        """
        pass
```

### 3.3 Confidence Scoring

```python
class ConfidenceAssessor:
    """
    Scores confidence in overall assessment based on:
    - Data freshness
    - Signal count and diversity
    - Evidence quality
    """
    
    def assess_confidence(self, signals: List[Signal], 
                         data_freshness: Dict[str, date]) -> float:
        """
        Returns 0-100 confidence score.
        Impacts how aggressively to weight scores.
        """
        pass
```

---

## 4. JSON Output Format

### 4.1 Company Report JSON Structure

```json
{
  "report_id": "prospect_20250421_00123456",
  "company_number": "00123456",
  "generated_at": "2025-04-21T14:32:00Z",
  
  "overall_assessment": {
    "overall_readiness_score": 82,
    "confidence_level": "high",
    "priority_tier": "tier_1",
    "summary": "Strong fit for FX & international payments use case with evidence of overseas operations and multi-entity complexity."
  },
  
  "company_overview": {
    "company_name": "TechExports Ltd",
    "legal_entity_type": "private limited",
    "status": "active",
    "industry": "Software/SaaS",
    "business_model": "saas",
    "revenue_gbp": 12500000,
    "employee_count": 45,
    "hq_location": "London, UK",
    "countries_of_operation": ["UK", "US", "Germany", "Singapore"]
  },
  
  "use_case_analysis": {
    "primary_use_case": {
      "use_case_name": "fx_international_money",
      "score": 91,
      "confidence": "high",
      "score_breakdown": {
        "cross_border_signals": 92,
        "pain_signals": 85,
        "provider_complexity": 78
      },
      "top_signals": [
        "international_subsidiaries",
        "fx_exposure_mentioned",
        "overseas_suppliers"
      ],
      "recommended_angle": "Consolidate FX exposure and international supplier payments"
    },
    "secondary_use_cases": [
      {
        "use_case_name": "core_banking",
        "score": 77,
        "recommendation": "Multi-entity account management"
      },
      {
        "use_case_name": "apis_developer_tooling",
        "score": 74,
        "recommendation": "Integration with existing platform"
      }
    ],
    "all_scores": {
      "core_banking": 77,
      "fx_international_money": 91,
      "merchant_acquiring": 64,
      "apis_developer_tooling": 74,
      "cards_spend_management": 58,
      "travel_conferma": 32,
      "accounting_integration": 71,
      "lending_credit": 54
    }
  },
  
  "signal_detection": {
    "detected_signals": [
      {
        "signal_id": "fx_exposure_mentioned",
        "signal_type": "cross_border_signals",
        "confidence": "high",
        "is_inferred": false,
        "evidence": {
          "text": "The group is exposed to foreign exchange fluctuations across its overseas operations.",
          "source_type": "filing",
          "source_title": "Companies House Strategic Report",
          "source_date": "2024-09-30",
          "source_url": "https://..."
        },
        "relevant_use_cases": ["fx_international_money", "core_banking"],
        "detected_at": "2025-04-21T14:30:00Z"
      },
      {
        "signal_id": "international_subsidiaries",
        "signal_type": "cross_border_signals",
        "confidence": "high",
        "is_inferred": false,
        "evidence": {
          "text": "The company has 3 international subsidiaries: TechExports Inc. (US), TechExports GmbH (Germany), TechExports Asia Pte Ltd (Singapore)",
          "source_type": "filing",
          "source_title": "Group Overview",
          "source_date": "2024-09-30"
        },
        "relevant_use_cases": ["fx_international_money", "core_banking"],
        "detected_at": "2025-04-21T14:30:00Z"
      }
    ],
    "trigger_events": [
      {
        "signal_type": "funding_round",
        "description": "Series B funding announced",
        "detected_at": "2025-03-15",
        "relevance": "Indicates growth trajectory and potential for new finance infrastructure"
      }
    ],
    "provider_detection": [
      {
        "provider_name": "Stripe",
        "category": "payment_processor",
        "confidence": "confirmed",
        "mentions": [
          {
            "text": "We process payments via Stripe for our online platform",
            "source": "company_website",
            "date": "2025-04"
          }
        ]
      },
      {
        "provider_name": "Wise",
        "category": "fx_provider",
        "confidence": "likely",
        "mentions": [
          {
            "text": "International payments team utilizes multi-currency transfer services",
            "source": "LinkedIn job posting",
            "date": "2025-02"
          }
        ]
      }
    ]
  },
  
  "pains_and_inferences": {
    "evidenced_pains": [
      {
        "pain_type": "fx_cost_leakage",
        "confidence": "high",
        "evidence_summary": "FX exposure mentioned in filings + multi-currency operations across 4 countries + no mention of FX hedging",
        "inferred_from_signals": ["fx_exposure_mentioned", "international_subsidiaries", "overseas_suppliers"]
      },
      {
        "pain_type": "working_capital_pressure",
        "confidence": "medium",
        "evidence_summary": "Filing mentions working capital challenges with multi-entity operations",
        "inferred_from_signals": ["working_capital_constraint", "growth_signals"]
      }
    ],
    "inferred_pains": [
      {
        "pain_type": "reconciliation_burden",
        "confidence": "medium",
        "evidence_summary": "Multi-entity, multi-currency setup with fragmented provider stack likely requires manual reconciliation",
        "inferred_from_signals": ["international_subsidiaries", "fragmented_payment_stack"]
      },
      {
        "pain_type": "banking_complexity",
        "confidence": "medium",
        "evidence_summary": "Evidence of provider fragmentation suggests multiple banking relationships",
        "inferred_from_signals": ["fragmented_payment_stack", "multiple_banks"]
      }
    ]
  },
  
  "recommended_action": {
    "outreach_angle": "FX savings and international supplier payment consolidation",
    "entry_point_product": "FX and International Money Movement",
    "supporting_messages": [
      "Consolidate FX exposure across your 4 international subsidiaries",
      "Optimize supplier payments to Germany and Singapore",
      "Improve cash visibility across multi-currency operations"
    ],
    "suggested_timing": "immediate",
    "timing_rationale": "Recent Series B funding + FX exposure + multi-entity complexity = strong product fit"
  },
  
  "evidence_audit": {
    "data_freshness": {
      "companies_house_filings": "2024-09-30",
      "news_and_web": "2025-04-15",
      "linkedin": "2025-04-10"
    },
    "signal_summary": {
      "cross_border_signals": 4,
      "growth_signals": 2,
      "pain_signals": 3,
      "trigger_events": 1,
      "total_signals": 10
    },
    "confidence_factors": {
      "data_recency": 0.95,
      "signal_diversity": 0.85,
      "evidence_quality": 0.90
    }
  }
}
```

### 4.2 Bulk Results Export Format

```json
{
  "export_timestamp": "2025-04-21T14:32:00Z",
  "total_companies": 143,
  "summary": {
    "tier_1_count": 34,
    "tier_2_count": 62,
    "tier_3_count": 47
  },
  "results": [
    {
      "company_number": "00123456",
      "company_name": "TechExports Ltd",
      "overall_score": 82,
      "priority_tier": "tier_1",
      "primary_use_case": "fx_international_money",
      "secondary_use_cases": ["core_banking", "apis_developer_tooling"],
      "top_signals": ["international_subsidiaries", "fx_exposure_mentioned"],
      "suggested_angle": "FX savings"
    },
    // ... more companies
  ],
  "filters_applied": {
    "min_score": 50,
    "company_types": ["private limited", "public limited", "llp"],
    "min_revenue_gbp": 15000000,
    "status": "active"
  }
}
```

---

## 5. Pipeline Steps

### 5.1 Data Collection Pipeline

```python
class DataCollectionPipeline:
    """
    Step 1: Fetch company data from all sources
    """
    
    async def run(self, company_identifiers: List[str]) -> List[Company]:
        """
        Input: List of company names or company numbers
        
        Steps:
        1. Search/match in Companies House
        2. Fetch company profile
        3. Fetch filing history
        4. Download recent filings (annual accounts, strategic reports)
        5. Fetch officers / PSC data
        6. Fetch subsidiary info
        7. Enrich with news (if API available)
        8. Enrich with LinkedIn data (if available)
        9. Extract structured data
        
        Output: List[Company] with all baseline data populated
        """
        pass
```

### 5.2 Text Extraction Pipeline

```python
class TextExtractionPipeline:
    """
    Step 2: Extract and normalize text from filings
    """
    
    def run(self, companies: List[Company]) -> List[Filing]:
        """
        For each recent filing:
        1. Download PDF/HTML
        2. Extract text sections:
           - Strategic report
           - Principal risks
           - Directors' report
           - Notes to accounts
           - Group overview
        3. Normalize and store as Filing objects
        4. Return list of fillings with extracted sections
        """
        pass
```

### 5.3 Signal Detection Pipeline

```python
class SignalDetectionPipeline:
    """
    Step 3: Detect all signals from company data + filings
    """
    
    def run(self, companies: List[Company], 
            filings: List[Filing]) -> Dict[str, List[Signal]]:
        """
        For each company:
        
        1. Cross-border signals
           - Search for FX keywords in filings
           - Check international subsidiary count
           - Search for overseas supplier mentions
           - Check for cross-border payroll
           
        2. Growth signals
           - Calculate revenue growth %
           - Calculate employee growth %
           - Search for market expansion keywords
           
        3. Finance transformation signals
           - Check for new finance leadership appointments
           - Search for hiring keywords (treasury, finance ops, etc.)
           
        4. Provider complexity signals
           - Detect multiple banks
           - Detect multiple payment processors
           - Check for ERP mentions
           
        5. Pain signals
           - Search for margin pressure keywords
           - Search for working capital keywords
           - Search for cost reduction keywords
           
        6. Trigger events
           - Search for funding announcements
           - Search for acquisition keywords
           - Check for new subsidiary creation
           - Check for leadership changes
        
        Output: Dict mapping company_number -> List[Signal]
        """
        pass
```

### 5.4 Provider Detection Pipeline

```python
class ProviderDetectionPipeline:
    """
    Step 4: Detect which providers/competitors each company uses
    """
    
    PROVIDER_DATABASE = {
        "payment_processor": ["Stripe", "Adyen", "Checkout.com", "PayPal", ...],
        "fx_provider": ["Wise", "Airwallex", "Payoneer", "WorldFirst", ...],
        "business_bank": ["Barclays", "HSBC", "Lloyds", "NatWest", ...],
        # ... etc
    }
    
    def run(self, companies: List[Company], 
            filings: List[Filing]) -> Dict[str, List[ProviderUsage]]:
        """
        For each company and filing:
        1. Search for provider name mentions
        2. Assess confidence (confirmed/likely/possible/stale)
        3. Count evidence sources
        4. Check if mention is recent (active) or stale
        5. Return ProviderUsage objects
        
        Output: Dict mapping company_number -> List[ProviderUsage]
        """
        pass
```

### 5.5 Pain Inference Pipeline

```python
class PainInferencePipeline:
    """
    Step 5: Infer likely pains from detected signals
    """
    
    PAIN_INFERENCE_RULES = {
        "fx_cost_leakage": {
            "required_signals": ["fx_exposure_mentioned", "international_subsidiaries"],
            "confidence_calc": "medium if any + high if all"
        },
        "reconciliation_burden": {
            "required_signals": ["international_subsidiaries", "fragmented_payment_stack"],
            "confidence_calc": "medium if any + high if all"
        },
        # ... more rules
    }
    
    def run(self, signals: Dict[str, List[Signal]]) -> Dict[str, List[InferredPain]]:
        """
        For each company and its signals:
        1. Check pain inference rules
        2. Calculate confidence based on supporting signals
        3. Generate evidence summary
        4. Mark as evidenced vs inferred
        
        Output: Dict mapping company_number -> List[InferredPain]
        """
        pass
```

### 5.6 Scoring Pipeline

```python
class ScoringPipeline:
    """
    Step 6: Score each use case and calculate overall readiness
    """
    
    def run(self, companies: List[Company], 
            signals: Dict[str, List[Signal]],
            providers: Dict[str, List[ProviderUsage]],
            pains: Dict[str, List[InferredPain]]) -> Dict[str, Dict[str, float]]:
        """
        For each company:
        1. Score each of 8 use cases (0-100)
        2. Apply recency decay to signals
        3. Apply use-case-specific weighted aggregation
        4. Calculate overall readiness score
        5. Assign priority tier
        6. Determine recommended outreach angle
        
        Output: Dict mapping company_number -> Dict of all scores
        """
        pass
```

### 5.7 Report Generation Pipeline

```python
class ReportGenerationPipeline:
    """
    Step 7: Generate final prospect report
    """
    
    def run(self, company: Company,
            signals: List[Signal],
            use_case_scores: Dict[str, float],
            overall_score: float,
            providers: List[ProviderUsage],
            pains: List[InferredPain]) -> ProspectReport:
        """
        1. Compile all data into ProspectReport object
        2. Select top contributing signals
        3. Determine primary/secondary use cases
        4. Generate recommended outreach angle
        5. Format for readability
        
        Output: ProspectReport (can be serialized to JSON)
        """
        pass
```

### 5.8 Complete Pipeline Orchestration

```python
class ProspectAnalysisPipeline:
    """
    Main orchestrator: runs all pipeline steps in sequence
    """
    
    async def analyze_batch(self, company_identifiers: List[str]) -> List[ProspectReport]:
        """
        Complete workflow:
        
        1. Data Collection
           Input: company names/numbers
           Output: Company objects
        
        2. Text Extraction
           Input: Companies
           Output: Filing objects with extracted text
        
        3. Signal Detection
           Input: Companies + Filings
           Output: Signals indexed by company
        
        4. Provider Detection
           Input: Companies + Filings
           Output: ProviderUsage indexed by company
        
        5. Pain Inference
           Input: Signals
           Output: InferredPain indexed by company
        
        6. Scoring
           Input: Companies + Signals + Providers + Pains
           Output: Scores (use-case and overall)
        
        7. Report Generation
           Input: All pipeline outputs
           Output: ProspectReport objects
        
        8. Export
           Input: Reports
           Output: JSON/CSV reports
        """
        pass
    
    async def analyze_single(self, company_identifier: str) -> ProspectReport:
        """
        Analyze single company through full pipeline
        """
        pass
```

---

## 6. Configuration & Extensibility

### 6.1 Signal Definition Configuration

```yaml
# signals.yaml - User-editable signal definitions
signals:
  cross_border_signals:
    fx_exposure_mentioned:
      keywords:
        - "foreign exchange"
        - "fx exposure"
        - "currency exposure"
      weight: 8.0
      relevant_use_cases: ["fx_international_money", "core_banking"]
  
  # Add/edit signals here
```

### 6.2 Weights Configuration

```yaml
# weights.yaml
use_case_weights:
  fx_international_money:
    cross_border_signals: 0.40
    growth_signals: 0.10
    finance_transformation_signals: 0.05
    # ... etc
  
use_case_importance:
  merchant_acquiring: 1.0
  fx_international_money: 1.0
  # ... etc
```

### 6.3 Provider Database Configuration

```yaml
# providers.yaml
providers:
  payment_processors:
    - name: "Stripe"
      aliases: ["stripe", "stripe payments"]
      category: "payment_processor"
    - name: "Adyen"
      aliases: ["adyen"]
      category: "payment_processor"
  # ... etc
```

---

## 7. Key Implementation Notes

### 7.1 Recency Decay Function

```python
def apply_recency_decay(signal: Signal, reference_date: date = today()) -> float:
    """
    Signals older than 2 years decay in weight.
    Formula: weight * (1 - (days_old / 730) * decay_rate)
    Minimum: 0.3 (30% of original weight)
    """
    days_old = (reference_date - signal.source_date).days
    if days_old < 180:
        return 1.0  # Full weight for recent signals
    elif days_old < 730:
        decay_rate = 0.5
        decay = 1.0 - (days_old / 730) * decay_rate
        return max(decay, 0.3)
    else:
        return 0.3  # Old signals capped at 30% weight
```

### 7.2 Confidence Calculation

```python
def calculate_confidence(num_signals: int, 
                         signal_diversity: float,
                         data_freshness: float) -> float:
    """
    Confidence ranges 0-100 based on:
    - num_signals: 0-100 points (1 signal = low, 5+ signals = high)
    - signal_diversity: 0-100 points (how many signal categories represented)
    - data_freshness: 0-100 points (how recent the data)
    
    Weighted average: 40% diversity + 40% freshness + 20% quantity
    """
    pass
```

### 7.3 Use Case Recommendation Logic

```python
def recommend_primary_use_case(scores: Dict[str, float], 
                               company: Company) -> str:
    """
    1. Filter to use cases with score > 60
    2. Consider company type/business model
    3. Check for "must-have" signals (e.g., must have FX signals for fx_international_money)
    4. Return highest-scoring qualifying use case
    """
    pass
```

---

## 8. Success Metrics

When building this system, validate:

- ✅ All 8 use cases can be scored independently
- ✅ Scores reflect company fitness for each product
- ✅ Evidence audit trail is complete (every signal traceable to source)
- ✅ Bulk analysis can process 100+ companies in <5 minutes
- ✅ Reports are actionable (recommended angle + entry product are clear)
- ✅ False positives are minimal (high-confidence signals only)
- ✅ Recency is properly factored (fresh signals weighted higher)
- ✅ Configuration can be edited without code changes

