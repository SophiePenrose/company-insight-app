"""
Signal definitions for the prospect readiness engine.
Contains all signals, their detection logic, weights, and use case mappings.
"""

from typing import Dict, List, Any

SIGNAL_DEFINITIONS = {
    "cross_border_signals": [
        {
            "signal_id": "fx_exposure_mentioned",
            "name": "FX Exposure Mentioned",
            "category": "cross_border",
            "keywords": ["foreign exchange", "fx exposure", "currency exposure", "exchange rate"],
            "relevant_use_cases": ["fx_international_money", "core_banking"],
            "base_weight": 8.0,
            "evidence_type": "text_extraction",
            "confidence_required": "medium"
        },
        {
            "signal_id": "international_subsidiaries",
            "name": "International Subsidiaries Present",
            "category": "cross_border",
            "detection_logic": "international_subsidiary_count > 0",
            "relevant_use_cases": ["fx_international_money", "core_banking"],
            "base_weight": 7.5,
            "evidence_type": "structured_data",
            "confidence_required": "high"
        },
        {
            "signal_id": "overseas_suppliers",
            "name": "Overseas Suppliers Mentioned",
            "category": "cross_border",
            "keywords": ["overseas supplier", "foreign supplier", "imported", "foreign purchase", "international supplier"],
            "relevant_use_cases": ["fx_international_money", "accounting_integration"],
            "base_weight": 7.0,
            "evidence_type": "text_extraction",
            "confidence_required": "medium"
        },
        {
            "signal_id": "international_revenue",
            "name": "International Revenue Streams",
            "category": "cross_border",
            "keywords": ["international revenue", "overseas revenue", "export", "foreign market"],
            "relevant_use_cases": ["fx_international_money", "merchant_acquiring"],
            "base_weight": 6.5,
            "evidence_type": "text_extraction",
            "confidence_required": "medium"
        },
        {
            "signal_id": "multi_currency_operations",
            "name": "Multi-Currency Operations",
            "category": "cross_border",
            "keywords": ["multi-currency", "multiple currencies", "eur", "usd", "foreign currency"],
            "relevant_use_cases": ["fx_international_money", "core_banking"],
            "base_weight": 8.5,
            "evidence_type": "text_extraction",
            "confidence_required": "high"
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
        },
        {
            "signal_id": "market_expansion",
            "name": "Market Expansion",
            "category": "growth",
            "keywords": ["market expansion", "new market", "geographic expansion", "international growth"],
            "relevant_use_cases": ["fx_international_money", "merchant_acquiring"],
            "base_weight": 6.5,
            "evidence_type": "text_extraction",
            "confidence_required": "medium"
        }
    ],

    "finance_transformation_signals": [
        {
            "signal_id": "new_finance_leadership",
            "name": "New Finance Leadership",
            "category": "finance_transformation",
            "keywords": ["new cfo", "appointed finance director", "new head of treasury", "finance director appointed"],
            "relevant_use_cases": ["core_banking", "accounting_integration"],
            "base_weight": 8.5,
            "evidence_type": "text_extraction",
            "confidence_required": "high"
        },
        {
            "signal_id": "finance_ops_hiring",
            "name": "Finance/Treasury Hiring",
            "category": "finance_transformation",
            "keywords": ["finance operations", "treasury", "financial controller", "treasury manager", "payments operations"],
            "relevant_use_cases": ["core_banking", "accounting_integration"],
            "base_weight": 7.0,
            "evidence_type": "text_extraction",
            "confidence_required": "medium"
        },
        {
            "signal_id": "finance_systems_hiring",
            "name": "Finance Systems Hiring",
            "category": "finance_transformation",
            "keywords": ["erp", "finance system", "accounting system", "financial systems"],
            "relevant_use_cases": ["accounting_integration", "core_banking"],
            "base_weight": 6.5,
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
        },
        {
            "signal_id": "multiple_fx_providers",
            "name": "Multiple FX Providers",
            "category": "provider_complexity",
            "detection_logic": "provider_usage.filter(category='fx_provider').count() > 1",
            "relevant_use_cases": ["fx_international_money"],
            "base_weight": 7.0,
            "evidence_type": "provider_detection",
            "confidence_required": "medium"
        }
    ],

    "pain_signals": [
        {
            "signal_id": "margin_pressure",
            "name": "Margin Pressure",
            "category": "pain",
            "keywords": ["margin pressure", "cost pressure", "rising costs", "margin squeeze"],
            "relevant_use_cases": ["merchant_acquiring", "fx_international_money"],
            "base_weight": 6.5,
            "evidence_type": "text_extraction",
            "confidence_required": "medium"
        },
        {
            "signal_id": "working_capital_constraint",
            "name": "Working Capital Constraint",
            "category": "pain",
            "keywords": ["working capital", "cash flow", "liquidity", "cash flow pressure"],
            "relevant_use_cases": ["merchant_acquiring", "fx_international_money", "lending"],
            "base_weight": 7.5,
            "evidence_type": "text_extraction",
            "confidence_required": "medium"
        },
        {
            "signal_id": "reconciliation_pain",
            "name": "Reconciliation Pain",
            "category": "pain",
            "keywords": ["reconciliation", "manual reconciliation", "reconciliation burden", "matching transactions"],
            "relevant_use_cases": ["accounting_integration", "core_banking"],
            "base_weight": 7.0,
            "evidence_type": "text_extraction",
            "confidence_required": "medium"
        },
        {
            "signal_id": "settlement_timing_issues",
            "name": "Settlement Timing Issues",
            "category": "pain",
            "keywords": ["settlement timing", "slow settlement", "settlement delay", "payment timing"],
            "relevant_use_cases": ["merchant_acquiring", "core_banking"],
            "base_weight": 6.5,
            "evidence_type": "text_extraction",
            "confidence_required": "medium"
        }
    ],

    "trigger_events": [
        {
            "signal_id": "funding_round",
            "name": "Recent Funding Round",
            "category": "trigger",
            "keywords": ["funding", "investment", "capital raise", "series", "private equity"],
            "relevant_use_cases": ["core_banking", "merchant_acquiring"],
            "base_weight": 9.0,
            "evidence_type": "text_extraction",
            "confidence_required": "high"
        },
        {
            "signal_id": "acquisition",
            "name": "Acquisition Event",
            "category": "trigger",
            "keywords": ["acquired", "acquisition", "purchased", "merger"],
            "relevant_use_cases": ["core_banking", "fx_international_money"],
            "base_weight": 8.5,
            "evidence_type": "text_extraction",
            "confidence_required": "high"
        },
        {
            "signal_id": "new_subsidiary",
            "name": "New Subsidiary Creation",
            "category": "trigger",
            "keywords": ["new subsidiary", "subsidiary created", "incorporated subsidiary"],
            "relevant_use_cases": ["core_banking", "fx_international_money"],
            "base_weight": 7.5,
            "evidence_type": "text_extraction",
            "confidence_required": "high"
        },
        {
            "signal_id": "international_office",
            "name": "International Office Opening",
            "category": "trigger",
            "keywords": ["international office", "new office", "office opening", "expansion"],
            "relevant_use_cases": ["fx_international_money", "core_banking"],
            "base_weight": 7.0,
            "evidence_type": "text_extraction",
            "confidence_required": "medium"
        }
    ]
}

# Use case definitions with their Revolut product mappings
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
    "cards_spend_management": {
        "cross_border_signals": 0.10,
        "growth_signals": 0.20,
        "finance_transformation_signals": 0.10,
        "provider_complexity_signals": 0.15,
        "pain_signals": 0.30,
        "trigger_events": 0.15
    },
    "accounting_integration": {
        "cross_border_signals": 0.15,
        "growth_signals": 0.10,
        "finance_transformation_signals": 0.25,
        "provider_complexity_signals": 0.20,
        "pain_signals": 0.20,
        "trigger_events": 0.10
    },
    "apis_developer_tooling": {
        "cross_border_signals": 0.10,
        "growth_signals": 0.25,
        "finance_transformation_signals": 0.15,
        "provider_complexity_signals": 0.20,
        "pain_signals": 0.20,
        "trigger_events": 0.10
    },
    "travel_conferma": {
        "cross_border_signals": 0.05,
        "growth_signals": 0.15,
        "finance_transformation_signals": 0.05,
        "provider_complexity_signals": 0.10,
        "pain_signals": 0.50,
        "trigger_events": 0.15
    },
    "lending_credit": {
        "cross_border_signals": 0.10,
        "growth_signals": 0.15,
        "finance_transformation_signals": 0.10,
        "provider_complexity_signals": 0.15,
        "pain_signals": 0.40,
        "trigger_events": 0.10
    }
}

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

# Provider database for detection
PROVIDER_DATABASE = {
    "payment_processors": [
        {"name": "Stripe", "aliases": ["stripe", "stripe payments"]},
        {"name": "Adyen", "aliases": ["adyen"]},
        {"name": "Checkout.com", "aliases": ["checkout.com", "checkout com"]},
        {"name": "PayPal", "aliases": ["paypal", "paypal checkout", "braintree"]},
        {"name": "Worldpay", "aliases": ["worldpay", "world pay"]},
        {"name": "Airwallex", "aliases": ["airwallex"]},
        {"name": "Payoneer", "aliases": ["payoneer"]},
        {"name": "Pleo", "aliases": ["pleo"]},
        {"name": "Spendesk", "aliases": ["spendesk"]},
        {"name": "Payhawk", "aliases": ["payhawk"]}
    ],
    "fx_providers": [
        {"name": "Wise", "aliases": ["wise", "wise business", "transferwise"]},
        {"name": "Airwallex", "aliases": ["airwallex"]},
        {"name": "Payoneer", "aliases": ["payoneer"]},
        {"name": "WorldFirst", "aliases": ["worldfirst"]},
        {"name": "OFX", "aliases": ["ofx"]},
        {"name": "CurrencyCloud", "aliases": ["currencycloud"]}
    ],
    "business_banks": [
        {"name": "Barclays", "aliases": ["barclays"]},
        {"name": "HSBC", "aliases": ["hsbc"]},
        {"name": "Lloyds", "aliases": ["lloyds"]},
        {"name": "NatWest", "aliases": ["natwest", "royal bank of scotland"]},
        {"name": "Santander", "aliases": ["santander"]},
        {"name": "Starling", "aliases": ["starling"]},
        {"name": "Monzo", "aliases": ["monzo"]}
    ],
    "accounting_systems": [
        {"name": "Xero", "aliases": ["xero"]},
        {"name": "QuickBooks", "aliases": ["quickbooks", "quick books"]},
        {"name": "Sage", "aliases": ["sage"]},
        {"name": "NetSuite", "aliases": ["netsuite", "net suite"]},
        {"name": "SAP", "aliases": ["sap"]}
    ]
}