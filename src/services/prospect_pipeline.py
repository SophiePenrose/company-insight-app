"""
Prospect Analysis Pipeline
Main orchestrator for the complete prospect readiness analysis.
"""

import asyncio
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from uuid import uuid4

from src.clients.companies_house import CompaniesHouseClient
from src.services.signal_detector import SignalDetector
from src.services.scoring import UseCaseScorer, OverallReadinessScorer, PainInferenceEngine
from src.models.prospect import (
    Company, Filing, Signal, ProviderUsage, InferredPain,
    UseCaseScore, ProspectReport
)


class ProspectAnalysisPipeline:
    """
    Complete pipeline for analyzing company prospects.
    Orchestrates data collection, signal detection, scoring, and report generation.
    """

    def __init__(self, ch_client: CompaniesHouseClient):
        self.ch_client = ch_client
        self.signal_detector = SignalDetector()
        self.use_case_scorer = UseCaseScorer()
        self.overall_scorer = OverallReadinessScorer()
        self.pain_engine = PainInferenceEngine()

    async def analyze_company(self, company_number: str) -> ProspectReport:
        """
        Analyze a single company through the complete pipeline.
        """
        try:
            # Step 1: Collect company data
            company = await self._collect_company_data(company_number)

            # Step 2: Collect and extract filings
            filings = await self._collect_filings(company)

            # Step 3: Detect provider usage
            provider_usage = self.signal_detector.detect_provider_usage(company, filings)

            # Step 4: Detect all signals
            signals = self.signal_detector.detect_all_signals(company, filings, provider_usage)

            # Step 5: Score use cases
            use_case_scores = self.use_case_scorer.score_all_use_cases(company, signals)

            # Step 6: Calculate overall readiness
            overall_assessment = self.overall_scorer.score_overall(use_case_scores, company)

            # Step 7: Infer pains
            inferred_pains = self.pain_engine.infer_pains(company, signals)

            # Step 8: Generate report
            report = self._generate_report(
                company, signals, provider_usage, use_case_scores,
                overall_assessment, inferred_pains
            )

            return report

        except Exception as e:
            # Return error report
            return ProspectReport(
                report_id=f"error_{company_number}_{uuid4().hex[:8]}",
                company_number=company_number,
                generated_at=datetime.now(),
                overall_readiness_score=0.0,
                confidence_level="low",
                priority_tier="tier_3",
                summary_assessment=f"Analysis failed: {str(e)}",
                company_overview=Company(
                    company_number=company_number,
                    company_name=f"Error loading {company_number}",
                    legal_entity_type="unknown",
                    status="unknown",
                    registered_address="Unknown",
                    incorporation_date=date.today(),
                    countries_of_operation=[],
                    number_of_subsidiaries=0,
                    international_subsidiary_count=0,
                    ownership_type="unknown",
                    sic_codes=[],
                    industry_classification="unknown",
                    business_model="unknown",
                    data_collection_date=datetime.now(),
                    freshness_score=0.0,
                    confidence_score=0.0
                ),
                recommended_outreach_angle="Unable to analyze - data collection failed",
                suggested_entry_point="unknown"
            )

    async def analyze_batch(self, company_numbers: List[str]) -> List[ProspectReport]:
        """
        Analyze multiple companies in batch.
        """
        reports = []
        for company_number in company_numbers:
            report = await self.analyze_company(company_number)
            reports.append(report)
        return reports

    async def _collect_company_data(self, company_number: str) -> Company:
        """
        Collect comprehensive company data from Companies House.
        """
        # Get company profile
        profile = self.ch_client.company_profile(company_number)

        # Extract basic info
        company_name = profile.get("company_name", "")
        status = profile.get("company_status", "unknown")
        incorporation_date = self._parse_date(profile.get("date_of_creation"))

        # Address
        address_data = profile.get("registered_office_address", {})
        registered_address = self._format_address(address_data)

        # SIC codes
        sic_codes = []
        for sic_entry in profile.get("sic_codes", []):
            if isinstance(sic_entry, dict):
                sic_codes.append(sic_entry.get("sic_code", ""))
            else:
                sic_codes.append(str(sic_entry))

        # Subsidiaries (simplified - would need additional API calls for full data)
        # For now, we'll use placeholder logic
        number_of_subsidiaries = 0  # Would need to query PSC data
        international_subsidiary_count = 0  # Would need to analyze subsidiary addresses

        # Business classification (simplified heuristics)
        industry_classification = self._classify_industry(sic_codes)
        business_model = self._classify_business_model(company_name, sic_codes)

        # Financials (would need to extract from filings)
        # Placeholder values
        latest_revenue_gbp = None
        revenue_growth_pct = None
        employee_count = profile.get("employee_count")

        company = Company(
            company_number=company_number,
            company_name=company_name,
            legal_entity_type=self._determine_entity_type(profile),
            status=status,
            registered_address=registered_address,
            hq_address=registered_address,  # Assume same for now
            incorporation_date=incorporation_date,
            countries_of_operation=["UK"],  # Assume UK-only for now
            latest_revenue_gbp=latest_revenue_gbp,
            revenue_growth_pct=revenue_growth_pct,
            profitability=None,
            cash_balance_gbp=None,
            debt_gbp=None,
            employee_count=employee_count,
            linkedin_employee_count=None,
            number_of_subsidiaries=number_of_subsidiaries,
            international_subsidiary_count=international_subsidiary_count,
            ownership_type=self._determine_ownership_type(profile),
            sic_codes=sic_codes,
            industry_classification=industry_classification,
            business_model=business_model,
            data_collection_date=datetime.now(),
            freshness_score=0.9,  # Assume fresh data
            confidence_score=0.8   # Assume good data quality
        )

        return company

    async def _collect_filings(self, company: Company) -> List[Filing]:
        """
        Collect and extract text from recent filings.
        """
        filings = []

        try:
            # Get filing history
            filing_history = self.ch_client.filing_history(company.company_number)
            filing_items = filing_history.get("items", [])

            # Process recent filings (last 3 years)
            cutoff_date = date.today().replace(year=date.today().year - 3)

            for item in filing_items[:20]:  # Limit to recent 20 filings
                filing_date = self._parse_date(item.get("date"))
                if filing_date and filing_date >= cutoff_date:
                    filing = Filing(
                        filing_id=item.get("transaction_id", item.get("barcode", "unknown")),
                        company_number=company.company_number,
                        filing_type=item.get("description", "unknown"),
                        filing_date=filing_date,
                        filing_url=None,  # Would need to construct URL
                        sections=self._extract_filing_sections(item),
                        extracted_at=datetime.now(),
                        source="companies_house"
                    )
                    filings.append(filing)

        except Exception as e:
            print(f"Error collecting filings for {company.company_number}: {e}")

        return filings

    def _extract_filing_sections(self, filing_item: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract text sections from filing item.
        This is a simplified version - real implementation would download and parse PDFs.
        """
        # Placeholder - in reality would need to download and OCR/parse filing documents
        description = filing_item.get("description", "")

        sections = {
            "description": description,
            "strategic_report": "",  # Would extract from actual document
            "principal_risks": "",   # Would extract from actual document
            "directors_report": "",  # Would extract from actual document
            "notes_to_accounts": "", # Would extract from actual document
            "group_overview": ""     # Would extract from actual document
        }

        return sections

    def _generate_report(self, company: Company, signals: List[Signal],
                        provider_usage: List[ProviderUsage],
                        use_case_scores: Dict[str, UseCaseScore],
                        overall_assessment: Dict[str, Any],
                        inferred_pains: Dict[str, Dict[str, Any]]) -> ProspectReport:
        """
        Generate the final prospect report.
        """
        # Convert inferred pains to model objects
        evidenced_pains = []
        inferred_pains_list = []

        for pain_data in inferred_pains.values():
            pain = InferredPain(
                pain_type=pain_data["pain_type"],
                company_number=company.company_number,
                confidence=pain_data["confidence"],
                inferred_from_signals=pain_data["supporting_signals"],
                evidence_summary=pain_data["evidence_summary"],
                is_directly_evidenced=pain_data["is_directly_evidenced"]
            )

            if pain.is_directly_evidenced:
                evidenced_pains.append(pain)
            else:
                inferred_pains_list.append(pain)

        # Identify trigger events (recent high-impact signals)
        trigger_events = [
            s for s in signals
            if s.signal_category == "trigger" and s.recency_decay_factor > 0.8
        ]

        # Generate summary assessment
        summary_assessment = self._generate_summary_assessment(
            overall_assessment, company, use_case_scores
        )

        # Determine outreach angle
        outreach_angle, entry_point = self._determine_outreach_strategy(
            overall_assessment, use_case_scores
        )

        # Signal summary
        signal_summary = {}
        for signal in signals:
            category = signal.signal_category
            signal_summary[category] = signal_summary.get(category, 0) + 1

        # Data freshness
        data_freshness = {
            "companies_house": company.data_collection_date.date(),
            "filings": min((f.filing_date for f in []), default=date.today()) if [] else date.today()
        }

        report = ProspectReport(
            report_id=f"prospect_{company.company_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            company_number=company.company_number,
            generated_at=datetime.now(),
            overall_readiness_score=overall_assessment["overall_score"],
            confidence_level=overall_assessment["confidence_level"],
            priority_tier=overall_assessment["priority_tier"],
            summary_assessment=summary_assessment,
            company_overview=company,
            primary_use_case=use_case_scores.get(overall_assessment.get("primary_use_case")),
            secondary_use_cases=[
                use_case_scores[uc] for uc in overall_assessment.get("secondary_use_cases", [])
                if uc in use_case_scores
            ],
            all_use_case_scores=overall_assessment.get("use_case_scores", {}),
            detected_signals=signals,
            trigger_events=trigger_events,
            provider_usage=provider_usage,
            evidenced_pains=evidenced_pains,
            inferred_pains=inferred_pains_list,
            recommended_outreach_angle=outreach_angle,
            suggested_entry_point=entry_point,
            signal_summary=signal_summary,
            data_freshness=data_freshness
        )

        return report

    # Helper methods

    def _parse_date(self, date_str: str) -> date:
        """Parse date string to date object."""
        if not date_str:
            return date.today()
        try:
            return datetime.fromisoformat(date_str).date()
        except:
            return date.today()

    def _format_address(self, address: Dict[str, Any]) -> str:
        """Format address dict to string."""
        if not address:
            return "Unknown"
        parts = [
            address.get("address_line_1"),
            address.get("address_line_2"),
            address.get("locality"),
            address.get("postal_code"),
            address.get("country")
        ]
        return ", ".join(str(p) for p in parts if p)

    def _determine_entity_type(self, profile: Dict[str, Any]) -> str:
        """Determine legal entity type."""
        company_type = profile.get("type", "").lower()
        if "private" in company_type and "limited" in company_type:
            return "private limited"
        elif "public" in company_type and "limited" in company_type:
            return "public limited"
        elif "llp" in company_type:
            return "llp"
        else:
            return "other"

    def _determine_ownership_type(self, profile: Dict[str, Any]) -> str:
        """Determine ownership type (simplified)."""
        # This would need more sophisticated analysis of PSC data
        return "private"

    def _classify_industry(self, sic_codes: List[str]) -> str:
        """Classify industry from SIC codes (simplified)."""
        if not sic_codes:
            return "unknown"

        # Very basic classification - would need proper SIC code mapping
        first_sic = sic_codes[0]
        if first_sic.startswith("62"):  # Computer programming
            return "technology"
        elif first_sic.startswith("63"):  # Information service
            return "technology"
        elif first_sic.startswith("46"):  # Wholesale trade
            return "wholesale/retail"
        else:
            return "other"

    def _classify_business_model(self, company_name: str, sic_codes: List[str]) -> str:
        """Classify business model (simplified heuristics)."""
        name_lower = company_name.lower()
        sic_str = " ".join(sic_codes).lower()

        if any(word in name_lower for word in ["software", "tech", "digital", "app", "platform"]):
            return "saas"
        elif any(word in name_lower for word in ["marketplace", "exchange", "platform"]):
            return "marketplace"
        elif any(word in name_lower for word in ["ecommerce", "online", "webshop", "retail"]):
            return "ecommerce"
        elif "wholesale" in sic_str or "import" in name_lower:
            return "importer"
        else:
            return "other"

    def _generate_summary_assessment(self, overall_assessment: Dict[str, Any],
                                   company: Company, use_case_scores: Dict[str, UseCaseScore]) -> str:
        """Generate human-readable summary."""
        score = overall_assessment["overall_score"]
        primary_uc = overall_assessment.get("primary_use_case")

        if score >= 75:
            strength = "strong"
        elif score >= 50:
            strength = "moderate"
        else:
            strength = "weak"

        if primary_uc:
            return f"{strength.title()} fit for Revolut Business with primary opportunity in {primary_uc.replace('_', ' ')}. {company.business_model.title()} business model in {company.industry_classification} sector."
        else:
            return f"{strength.title()} fit for Revolut Business. Limited signal detection for specific use cases."

    def _determine_outreach_strategy(self, overall_assessment: Dict[str, Any],
                                   use_case_scores: Dict[str, UseCaseScore]) -> tuple[str, str]:
        """Determine recommended outreach angle and entry point."""
        primary_uc = overall_assessment.get("primary_use_case", "general")

        strategies = {
            "fx_international_money": ("FX savings and international supplier payments", "FX and International Money Movement"),
            "merchant_acquiring": ("Consolidated payment processing and settlement", "Merchant Acquiring"),
            "core_banking": ("Multi-entity banking and cash management", "Business Banking"),
            "cards_spend_management": ("Employee spend controls and virtual cards", "Cards and Spend Management"),
            "apis_developer_tooling": ("Custom payment integration and APIs", "APIs and Developer Tools"),
            "accounting_integration": ("Automated bank feeds and reconciliation", "Accounting Integration")
        }

        angle, entry = strategies.get(primary_uc, ("General banking and payment solutions", "Business Banking"))
        return angle, entry