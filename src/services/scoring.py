"""
Scoring Service
Calculates use-case scores and overall readiness scores.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from src.config.signals import USE_CASE_WEIGHTS, USE_CASE_IMPORTANCE, USE_CASES
from src.models.prospect import Signal, UseCaseScore, Company


class UseCaseScorer:
    """
    Scores each use case 0-100 based on detected signals.
    """

    def score_use_case(self, company: Company, signals: List[Signal],
                       use_case: str) -> UseCaseScore:
        """
        Score a specific use case based on relevant signals.
        """
        # Filter signals relevant to this use case
        relevant_signals = [
            s for s in signals
            if use_case in s.relevant_use_cases
        ]

        if not relevant_signals:
            return UseCaseScore(
                use_case_name=use_case,
                company_number=company.company_number,
                overall_score=0.0,
                confidence_level="low",
                signal_scores={},
                top_contributing_signals=[],
                recommended_emphasis=f"No signals detected for {use_case}"
            )

        # Group signals by category and calculate category scores
        signal_scores = self._calculate_category_scores(relevant_signals, use_case)

        # Apply use-case-specific weights
        weights = USE_CASE_WEIGHTS.get(use_case, {})
        overall_score = sum(
            signal_scores.get(category, 0.0) * weight
            for category, weight in weights.items()
        )

        # Cap at 100
        overall_score = min(overall_score, 100.0)

        # Determine confidence level
        confidence_level = self._calculate_confidence_level(relevant_signals)

        # Get top contributing signals
        top_signals = sorted(
            relevant_signals,
            key=lambda s: s.weight_multiplier * s.recency_decay_factor,
            reverse=True
        )[:3]
        top_signal_ids = [s.signal_id for s in top_signals]

        # Generate recommended emphasis
        recommended_emphasis = self._generate_recommendation(use_case, signal_scores)

        return UseCaseScore(
            use_case_name=use_case,
            company_number=company.company_number,
            overall_score=overall_score,
            confidence_level=confidence_level,
            signal_scores=signal_scores,
            top_contributing_signals=top_signal_ids,
            recommended_emphasis=recommended_emphasis
        )

    def score_all_use_cases(self, company: Company, signals: List[Signal]) -> Dict[str, UseCaseScore]:
        """
        Score all 8 use cases and return detailed results.
        """
        results = {}
        for use_case in USE_CASES:
            results[use_case] = self.score_use_case(company, signals, use_case)
        return results

    def _calculate_category_scores(self, signals: List[Signal], use_case: str) -> Dict[str, float]:
        """
        Calculate scores for each signal category.
        """
        category_scores = {}

        # Group signals by category
        categories = {}
        for signal in signals:
            category = signal.signal_category
            if category not in categories:
                categories[category] = []
            categories[category].append(signal)

        # Calculate score for each category
        for category, category_signals in categories.items():
            # Average the weighted signals in this category
            if category_signals:
                total_weight = sum(
                    s.weight_multiplier * s.recency_decay_factor
                    for s in category_signals
                )
                avg_weight = total_weight / len(category_signals)

                # Scale to 0-100 based on expected signal strength
                # This is a heuristic - could be made configurable
                category_scores[category] = min(avg_weight * 10, 100.0)
            else:
                category_scores[category] = 0.0

        return category_scores

    def _calculate_confidence_level(self, signals: List[Signal]) -> str:
        """
        Calculate confidence level based on signal quality and quantity.
        """
        if not signals:
            return "low"

        # Count high-confidence signals
        high_conf_signals = [s for s in signals if s.confidence == "high"]
        high_ratio = len(high_conf_signals) / len(signals)

        # Consider recency
        recent_signals = [s for s in signals if s.recency_decay_factor > 0.8]
        recent_ratio = len(recent_signals) / len(signals)

        # Combined score
        confidence_score = (high_ratio * 0.6) + (recent_ratio * 0.4)

        if confidence_score > 0.7:
            return "high"
        elif confidence_score > 0.4:
            return "medium"
        else:
            return "low"


class OverallReadinessScorer:
    """
    Aggregates use-case scores into overall readiness score.
    """

    def score_overall(self, use_case_scores: Dict[str, UseCaseScore],
                     company: Company) -> Dict[str, Any]:
        """
        Calculate overall readiness score from use-case scores.
        """
        if not use_case_scores:
            return {
                "overall_score": 0.0,
                "confidence_level": "low",
                "priority_tier": "tier_3",
                "primary_use_case": None,
                "secondary_use_cases": []
            }

        # Get scores for all use cases
        scores_dict = {uc: score.overall_score for uc, score in use_case_scores.items()}

        # Apply importance weights and company-type modifiers
        weighted_scores = {}
        for use_case, score in scores_dict.items():
            importance = USE_CASE_IMPORTANCE.get(use_case, 0.5)
            company_modifier = self._get_company_modifier(company, use_case)
            weighted_scores[use_case] = score * importance * company_modifier

        # Calculate overall score as weighted average of top 3 use cases
        sorted_scores = sorted(weighted_scores.items(), key=lambda x: x[1], reverse=True)
        top_3_scores = sorted_scores[:3]

        if not top_3_scores:
            overall_score = 0.0
        else:
            total_weight = sum(score for _, score in top_3_scores)
            overall_score = total_weight / len(top_3_scores) if top_3_scores else 0.0

        # Cap at 100
        overall_score = min(overall_score, 100.0)

        # Determine primary and secondary use cases
        primary_use_case = top_3_scores[0][0] if top_3_scores else None
        secondary_use_cases = [uc for uc, _ in top_3_scores[1:]] if len(top_3_scores) > 1 else []

        # Determine priority tier
        priority_tier = self.assign_priority_tier(overall_score)

        # Calculate confidence
        confidence_scores = [score.confidence_level for score in use_case_scores.values()]
        overall_confidence = self._aggregate_confidence(confidence_scores)

        return {
            "overall_score": overall_score,
            "confidence_level": overall_confidence,
            "priority_tier": priority_tier,
            "primary_use_case": primary_use_case,
            "secondary_use_cases": secondary_use_cases,
            "use_case_scores": scores_dict
        }

    def assign_priority_tier(self, overall_score: float) -> str:
        """
        Assign priority tier based on overall score.
        """
        if overall_score >= 75:
            return "tier_1"  # Immediate outreach
        elif overall_score >= 50:
            return "tier_2"  # Strong potential, needs context
        else:
            return "tier_3"  # Weak fit or incomplete data

    def _get_company_modifier(self, company: Company, use_case: str) -> float:
        """
        Apply company-type specific modifiers to use case scores.
        """
        # Business model modifiers
        business_model = company.business_model.lower()

        modifiers = {
            "ecommerce": {
                "merchant_acquiring": 1.3,
                "fx_international_money": 1.1,
                "cards_spend_management": 1.1
            },
            "saas": {
                "merchant_acquiring": 1.2,
                "apis_developer_tooling": 1.3,
                "fx_international_money": 1.1
            },
            "marketplace": {
                "merchant_acquiring": 1.4,
                "apis_developer_tooling": 1.2,
                "core_banking": 1.1
            },
            "importer": {
                "fx_international_money": 1.4,
                "core_banking": 1.2
            }
        }

        if business_model in modifiers and use_case in modifiers[business_model]:
            return modifiers[business_model][use_case]

        return 1.0  # No modifier

    def _aggregate_confidence(self, confidence_levels: List[str]) -> str:
        """
        Aggregate multiple confidence levels into one.
        """
        if not confidence_levels:
            return "low"

        # Count levels
        high_count = confidence_levels.count("high")
        medium_count = confidence_levels.count("medium")
        low_count = confidence_levels.count("low")

        total = len(confidence_levels)

        # Weighted score
        score = (high_count * 3 + medium_count * 2 + low_count * 1) / (total * 3)

        if score > 0.7:
            return "high"
        elif score > 0.4:
            return "medium"
        else:
            return "low"


class PainInferenceEngine:
    """
    Infers likely pains from detected signals.
    """

    PAIN_INFERENCE_RULES = {
        "fx_cost_leakage": {
            "required_signals": ["fx_exposure_mentioned", "international_subsidiaries"],
            "evidence_summary_template": "FX exposure mentioned in filings + {subsidiary_count} international subsidiaries + no mention of FX hedging",
            "confidence": "high"
        },
        "reconciliation_burden": {
            "required_signals": ["international_subsidiaries", "fragmented_payment_stack"],
            "evidence_summary_template": "Multi-entity setup with {subsidiary_count} subsidiaries + fragmented payment stack suggests manual reconciliation burden",
            "confidence": "medium"
        },
        "working_capital_pressure": {
            "required_signals": ["working_capital_constraint", "margin_pressure"],
            "evidence_summary_template": "Direct mentions of working capital constraints and margin pressure in filings",
            "confidence": "high"
        },
        "banking_complexity": {
            "required_signals": ["multiple_banks"],
            "evidence_summary_template": "Multiple banking relationships detected, suggesting fragmented banking setup",
            "confidence": "medium"
        },
        "settlement_timing_issues": {
            "required_signals": ["settlement_timing_issues", "merchant_acquiring"],
            "evidence_summary_template": "Settlement timing issues mentioned alongside payment processing operations",
            "confidence": "medium"
        }
    }

    def infer_pains(self, company: Company, signals: List[Signal]) -> Dict[str, Dict[str, Any]]:
        """
        Infer likely pains from detected signals.
        """
        inferred_pains = {}

        # Get signal types present
        signal_types = {s.signal_type for s in signals}

        for pain_type, rule in self.PAIN_INFERENCE_RULES.items():
            required_signals = set(rule["required_signals"])
            matched_signals = required_signals.intersection(signal_types)

            if matched_signals:
                # Calculate confidence based on how many required signals are present
                match_ratio = len(matched_signals) / len(required_signals)

                # Generate evidence summary
                evidence_summary = rule["evidence_summary_template"].format(
                    subsidiary_count=company.international_subsidiary_count
                )

                inferred_pains[pain_type] = {
                    "pain_type": pain_type,
                    "confidence": rule["confidence"] if match_ratio == 1.0 else "medium",
                    "evidence_summary": evidence_summary,
                    "supporting_signals": list(matched_signals),
                    "is_directly_evidenced": match_ratio == 1.0
                }

        return inferred_pains