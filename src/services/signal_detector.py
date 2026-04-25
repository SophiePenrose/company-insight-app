"""
Signal Detection Service
Detects all predefined signals from company data and filings.
"""

import re
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from dateutil import parser as date_parser

from src.config.signals import SIGNAL_DEFINITIONS, PROVIDER_DATABASE
from src.models.prospect import Signal, ProviderUsage, Filing, Company


class SignalDetector:
    """
    Detects signals from company data, filings, and other sources.
    """

    def __init__(self):
        self.signal_definitions = SIGNAL_DEFINITIONS
        self.provider_database = PROVIDER_DATABASE

    def detect_all_signals(self, company: Company, filings: List[Filing],
                          provider_usage: List[ProviderUsage]) -> List[Signal]:
        """
        Detect all signals for a company from all available data sources.
        """
        signals = []

        # Detect signals from filings
        for filing in filings:
            filing_signals = self._detect_signals_from_filing(company, filing)
            signals.extend(filing_signals)

        # Detect signals from structured company data
        structured_signals = self._detect_structured_signals(company, provider_usage)
        signals.extend(structured_signals)

        # Apply recency decay to all signals
        for signal in signals:
            signal.recency_decay_factor = self._calculate_recency_decay(signal.source_date)

        return signals

    def _detect_signals_from_filing(self, company: Company, filing: Filing) -> List[Signal]:
        """
        Detect signals from a single filing's text content.
        """
        signals = []

        # Combine all text sections for searching
        full_text = " ".join(filing.sections.values()).lower()

        for category, category_signals in self.signal_definitions.items():
            for signal_def in category_signals:
                if signal_def.get("evidence_type") == "text_extraction":
                    detected_signals = self._detect_text_signal(
                        company.company_number, filing, signal_def, full_text
                    )
                    if detected_signals:
                        signals.extend(detected_signals)

        return signals

    def _detect_text_signal(self, company_number: str, filing: Filing,
                           signal_def: Dict[str, Any], full_text: str) -> List[Signal]:
        """
        Detect a specific text-based signal in filing content.
        """
        signals = []
        keywords = signal_def.get("keywords", [])

        for keyword in keywords:
            if keyword.lower() in full_text:
                # Find the excerpt containing this keyword
                excerpt = self._extract_context(full_text, keyword)

                signal = Signal(
                    signal_id=f"{company_number}_{signal_def['signal_id']}_{filing.filing_id}",
                    company_number=company_number,
                    signal_type=signal_def["signal_id"],
                    signal_category=signal_def["category"],
                    evidence_text=excerpt,
                    source_type="filing",
                    source_title=filing.filing_type,
                    source_date=filing.filing_date,
                    source_url=filing.filing_url,
                    detected_at=datetime.now(),
                    confidence=signal_def.get("confidence_required", "medium"),
                    is_inferred=False,
                    recency_decay_factor=1.0,  # Will be calculated later
                    relevant_use_cases=signal_def.get("relevant_use_cases", []),
                    weight_multiplier=signal_def.get("base_weight", 1.0)
                )
                signals.append(signal)
                break  # Only create one signal per keyword type

        return signals

    def _detect_structured_signals(self, company: Company,
                                  provider_usage: List[ProviderUsage]) -> List[Signal]:
        """
        Detect signals from structured company data and provider usage.
        """
        signals = []

        # International subsidiaries signal
        if company.international_subsidiary_count > 0:
            signal = Signal(
                signal_id=f"{company.company_number}_international_subsidiaries_structured",
                company_number=company.company_number,
                signal_type="international_subsidiaries",
                signal_category="cross_border",
                evidence_text=f"Company has {company.international_subsidiary_count} international subsidiaries",
                source_type="companies_house",
                source_title="Company Profile",
                source_date=company.incorporation_date,  # Use incorporation as proxy
                detected_at=datetime.now(),
                confidence="high",
                is_inferred=False,
                recency_decay_factor=1.0,
                relevant_use_cases=["fx_international_money", "core_banking"],
                weight_multiplier=7.5
            )
            signals.append(signal)

        # Revenue growth signal
        if company.revenue_growth_pct and company.revenue_growth_pct > 25:
            signal = Signal(
                signal_id=f"{company.company_number}_strong_revenue_growth",
                company_number=company.company_number,
                signal_type="strong_revenue_growth",
                signal_category="growth",
                evidence_text=f"Revenue growth of {company.revenue_growth_pct:.1f}% detected",
                source_type="companies_house",
                source_title="Financial Data",
                source_date=date.today(),  # Current data
                detected_at=datetime.now(),
                confidence="high",
                is_inferred=False,
                recency_decay_factor=1.0,
                relevant_use_cases=["merchant_acquiring", "core_banking", "cards_spend"],
                weight_multiplier=6.0
            )
            signals.append(signal)

        # Provider complexity signals
        bank_providers = [p for p in provider_usage if p.provider_category == "business_bank"]
        if len(bank_providers) > 1:
            signal = Signal(
                signal_id=f"{company.company_number}_multiple_banks",
                company_number=company.company_number,
                signal_type="multiple_banks",
                signal_category="provider_complexity",
                evidence_text=f"Multiple business banks detected: {', '.join([p.provider_name for p in bank_providers])}",
                source_type="analysis",
                source_title="Provider Analysis",
                source_date=date.today(),
                detected_at=datetime.now(),
                confidence="medium",
                is_inferred=True,
                recency_decay_factor=1.0,
                relevant_use_cases=["core_banking"],
                weight_multiplier=7.5
            )
            signals.append(signal)

        payment_providers = [p for p in provider_usage if p.provider_category == "payment_processor"]
        if len(payment_providers) > 1:
            signal = Signal(
                signal_id=f"{company.company_number}_fragmented_payment_stack",
                company_number=company.company_number,
                signal_type="fragmented_payment_stack",
                signal_category="provider_complexity",
                evidence_text=f"Multiple payment processors detected: {', '.join([p.provider_name for p in payment_providers])}",
                source_type="analysis",
                source_title="Provider Analysis",
                source_date=date.today(),
                detected_at=datetime.now(),
                confidence="medium",
                is_inferred=True,
                recency_decay_factor=1.0,
                relevant_use_cases=["merchant_acquiring", "core_banking"],
                weight_multiplier=8.0
            )
            signals.append(signal)

        fx_providers = [p for p in provider_usage if p.provider_category == "fx_provider"]
        if len(fx_providers) > 1:
            signal = Signal(
                signal_id=f"{company.company_number}_multiple_fx_providers",
                company_number=company.company_number,
                signal_type="multiple_fx_providers",
                signal_category="provider_complexity",
                evidence_text=f"Multiple FX providers detected: {', '.join([p.provider_name for p in fx_providers])}",
                source_type="analysis",
                source_title="Provider Analysis",
                source_date=date.today(),
                detected_at=datetime.now(),
                confidence="medium",
                is_inferred=True,
                recency_decay_factor=1.0,
                relevant_use_cases=["fx_international_money"],
                weight_multiplier=7.0
            )
            signals.append(signal)

        return signals

    def detect_provider_usage(self, company: Company, filings: List[Filing]) -> List[ProviderUsage]:
        """
        Detect which providers/competitors the company uses.
        """
        provider_usage = []

        # Combine all filing text
        all_text = ""
        for filing in filings:
            all_text += " ".join(filing.sections.values()) + " "

        all_text = all_text.lower()

        for category, providers in self.provider_database.items():
            for provider in providers:
                mentions = []
                provider_name = provider["name"].lower()

                # Check for direct name mentions
                if provider_name in all_text:
                    mentions.append({
                        "text": f"Direct mention of {provider['name']}",
                        "source": "filing",
                        "date": date.today().isoformat()
                    })

                # Check for aliases
                for alias in provider.get("aliases", []):
                    if alias in all_text:
                        mentions.append({
                            "text": f"Alias '{alias}' found for {provider['name']}",
                            "source": "filing",
                            "date": date.today().isoformat()
                        })

                if mentions:
                    # Determine confidence level
                    confidence = "confirmed" if len(mentions) >= 2 else "likely"

                    # Check if mentions are recent (within 2 years)
                    is_active = any(
                        (date.today() - date_parser.parse(mention["date"])).days < 730
                        for mention in mentions
                    )

                    usage = ProviderUsage(
                        provider_name=provider["name"],
                        provider_category=category,
                        confidence=confidence,
                        evidence_count=len(mentions),
                        evidence_texts=mentions,
                        last_mentioned=date.today(),
                        is_active_mention=is_active
                    )
                    provider_usage.append(usage)

        return provider_usage

    def _extract_context(self, text: str, keyword: str, context_chars: int = 200) -> str:
        """
        Extract context around a keyword in the text.
        """
        keyword_lower = keyword.lower()
        start_idx = text.find(keyword_lower)

        if start_idx == -1:
            return f"Contains: {keyword}"

        # Get context around the keyword
        start = max(0, start_idx - context_chars // 2)
        end = min(len(text), start_idx + len(keyword) + context_chars // 2)

        context = text[start:end]
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."

        return context.strip()

    def _calculate_recency_decay(self, source_date: date, reference_date: Optional[date] = None) -> float:
        """
        Calculate recency decay factor for signals.
        Signals older than 2 years decay in weight.
        """
        if reference_date is None:
            reference_date = date.today()

        days_old = (reference_date - source_date).days

        if days_old < 180:
            return 1.0  # Full weight for recent signals
        elif days_old < 730:
            # Linear decay from 1.0 to 0.3 over 2 years
            decay_rate = 0.7 / 550  # 0.7 weight loss over 550 days (730-180)
            decay = 1.0 - (days_old - 180) * decay_rate
            return max(decay, 0.3)
        else:
            return 0.3  # Minimum weight for old signals