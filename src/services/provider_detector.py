from typing import Any, Dict, List


PROVIDER_KEYWORDS = {
    "stripe": ["stripe", "stripe payments", "stripe connect", "stripe checkout", "stripe terminal"],
    "adyen": ["adyen", "adyen for platforms", "adyen checkout", "adyen cse"],
    "checkout.com": ["checkout.com", "checkout com"],
    "paypal": ["paypal", "paypal checkout", "braintree"],
    "worldpay": ["worldpay", "world pay"],
    "airwallex": ["airwallex"],
    "wise": ["wise", "wise business", "transferwise"],
    "go cardless": ["gocardless", "go cardless", "direct debit"],
    "square": ["square", "block inc"],
}


class ProviderDetector:
    def __init__(self):
        pass

    def detect_from_text(self, text: str) -> Dict[str, Any]:
        haystack = (text or "").lower()
        matches: List[Dict[str, Any]] = []

        for provider, keywords in PROVIDER_KEYWORDS.items():
            for keyword in keywords:
                if keyword in haystack:
                    matches.append({"provider": provider, "matched_keyword": keyword})
                    break

        primary = matches[0]["provider"] if matches else None

        return {
            "is_provider_active": bool(matches),
            "primary_provider": primary,
            "matched_providers": matches,
            "confidence": "high" if len(matches) >= 2 else "medium" if matches else "low",
        }

    def detect_from_profile_rows(self, profile_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        joined = " ".join(
            f"{row.get('name', '')} {row.get('title', '')} {row.get('summary', '')}"
            for row in profile_rows
        )
        return self.detect_from_text(joined)
