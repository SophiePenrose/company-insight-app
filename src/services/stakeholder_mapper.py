from typing import Any, Dict, List, Optional


TITLE_RULES = {
    "economic_buyer": [
        "chief financial officer",
        "cfo",
        "finance director",
        "financial director",
        "chief executive officer",
        "ceo",
    ],
    "operational_buyer": [
        "head of finance",
        "vp finance",
        "financial controller",
        "treasurer",
        "head of treasury",
        "finance manager",
    ],
    "technical_influencer": [
        "head of payments",
        "payments lead",
        "finance systems manager",
        "finance systems lead",
        "erp lead",
        "head of financial systems",
    ],
    "operational_influencer": [
        "coo",
        "chief operating officer",
        "head of operations",
        "procurement director",
    ],
}


class StakeholderMapper:
    def __init__(self):
        pass

    def _normalize(self, value: str) -> str:
        return (value or "").strip().lower()

    def _category_for_title(self, title: str) -> Optional[str]:
        t = self._normalize(title)
        for category, titles in TITLE_RULES.items():
            for rule in titles:
                if rule in t:
                    return category
        return None

    def _seniority_score(self, category: str) -> float:
        return {
            "economic_buyer": 95,
            "operational_buyer": 80,
            "technical_influencer": 75,
            "operational_influencer": 70,
        }.get(category, 50)

    def _decision_relevance(self, category: str) -> str:
        return {
            "economic_buyer": "high",
            "operational_buyer": "high",
            "technical_influencer": "medium-high",
            "operational_influencer": "medium",
        }.get(category, "medium")

    def map_officers(self, officers_payload: Dict[str, Any], source_title: str = "Companies House officers") -> List[Dict[str, Any]]:
        items = officers_payload.get("items", []) if isinstance(officers_payload, dict) else []
        mapped = []

        for item in items:
            name = item.get("name", "")
            title = item.get("officer_role") or item.get("name_elements", {}).get("title", "") or item.get("appointed_on", "")
            category = self._category_for_title(title)

            if not category:
                continue

            mapped.append(
                {
                    "name": name,
                    "title": title,
                    "stakeholder_category": category,
                    "seniority_score": self._seniority_score(category),
                    "decision_relevance": self._decision_relevance(category),
                    "source_type": "companies_house_officers",
                    "source_title": source_title,
                    "source_url": item.get("links", {}).get("self"),
                    "is_current": item.get("resigned_on") is None,
                    "confidence": "high" if item.get("resigned_on") is None else "medium",
                    "why_relevant": self._why_relevant(category),
                    "evidence_ids": [],
                }
            )

        return sorted(mapped, key=lambda x: x["seniority_score"], reverse=True)

    def map_candidates_from_profiles(self, profile_rows: List[Dict[str, Any]], source_type: str) -> List[Dict[str, Any]]:
        mapped = []

        for row in profile_rows:
            name = row.get("name", "")
            title = row.get("title", "")
            category = self._category_for_title(title)

            if not category:
                continue

            mapped.append(
                {
                    "name": name,
                    "title": title,
                    "stakeholder_category": category,
                    "seniority_score": self._seniority_score(category),
                    "decision_relevance": self._decision_relevance(category),
                    "source_type": source_type,
                    "source_title": row.get("source_title", source_type),
                    "source_url": row.get("source_url"),
                    "is_current": row.get("is_current", True),
                    "confidence": row.get("confidence", "medium"),
                    "why_relevant": self._why_relevant(category),
                    "evidence_ids": row.get("evidence_ids", []),
                }
            )

        return sorted(mapped, key=lambda x: x["seniority_score"], reverse=True)

    def _why_relevant(self, category: str) -> str:
        return {
            "economic_buyer": "Likely owns banking, FX, liquidity, and finance transformation decisions.",
            "operational_buyer": "Likely owns finance operations and workflow decisions.",
            "technical_influencer": "Likely influences integrations, systems, payments, and finance automation.",
            "operational_influencer": "Likely influences operational rollout and finance process change.",
        }.get(category, "Likely relevant stakeholder.")
