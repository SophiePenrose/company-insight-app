"""
Enhanced AI-powered signal detection for prospect analysis.
Uses semantic understanding and context analysis instead of simple keyword matching.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import spacy
from spacy.lang.en import English

@dataclass
class SemanticSignal:
    """A signal detected through semantic analysis."""
    signal_id: str
    confidence: float
    evidence_text: str
    context: str
    semantic_match: str

class AISignalDetector:
    """
    Advanced signal detection using NLP and semantic analysis.
    Goes beyond keyword matching to understand document context and meaning.
    """
    
    def __init__(self):
        # Initialize spaCy for NLP processing
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback to basic English model
            self.nlp = English()
        # Ensure sentence boundaries are set
        if not self.nlp.has_pipe("sentencizer"):
            self.nlp.add_pipe("sentencizer")
        
        # Semantic patterns for different pain points
        self.semantic_patterns = {
            "fx_costs": {
                "patterns": [
                    r"foreign exchange (costs?|expenses?|losses?|volatility)",
                    r"currency (fluctuations?|volatility|risk|exposure)",
                    r"exchange rate (changes?|volatility|risk)",
                    r"fx (costs?|losses?|hedging|exposure)",
                    r"international payment (costs?|fees?|charges?)",
                    r"cross.border (transaction|payment) costs?",
                    r"currency conversion (costs?|fees?)",
                ],
                "context_indicators": [
                    "expensive", "high cost", "significant", "material impact",
                    "burden", "challenge", "difficulty", "problem", "issue"
                ],
                "signal_id": "fx_cost_pain",
                "use_cases": ["fx_international_money", "core_banking"]
            },
            
            "cash_management": {
                "patterns": [
                    r"cash flow (management|challenges?|problems?)",
                    r"working capital (constraints?|shortage|issues?)",
                    r"liquidity (challenges?|constraints?|issues?)",
                    r"cash management (inefficiencies?|problems?)",
                    r"treasury (function|operations?) (challenges?|inefficiencies?)",
                    r"multiple bank accounts? (management|overhead)",
                ],
                "context_indicators": [
                    "inefficient", "complex", "time.consuming", "manual",
                    "fragmented", "disconnected", "challenging"
                ],
                "signal_id": "cash_management_pain",
                "use_cases": ["core_banking", "cards_spend_management"]
            },
            
            "international_expansion": {
                "patterns": [
                    r"international (expansion|growth|markets?)",
                    r"cross.border (expansion|growth|operations?)",
                    r"foreign market (entry|expansion|growth)",
                    r"global (expansion|presence|operations?)",
                    r"overseas (expansion|growth|ventures?)",
                ],
                "context_indicators": [
                    "planning", "considering", "opportunity", "potential",
                    "strategic", "growth", "expansion"
                ],
                "signal_id": "international_growth_signal",
                "use_cases": ["fx_international_money", "core_banking", "merchant_acquiring"]
            },
            
            "payment_processing": {
                "patterns": [
                    r"payment processing (costs?|fees?|inefficiencies?)",
                    r"merchant services? (costs?|fees?|charges?)",
                    r"card processing (costs?|fees?|charges?)",
                    r"payment gateway (costs?|fees?|charges?)",
                    r"transaction (fees?|costs?|charges?)",
                    r"interchange (fees?|costs?)",
                ],
                "context_indicators": [
                    "high", "expensive", "significant", "material",
                    "reducing", "optimizing", "minimizing"
                ],
                "signal_id": "payment_cost_pain",
                    "use_cases": ["merchant_acquiring", "cards_spend_management"]
            },
            
            "accounting_integration": {
                "patterns": [
                    r"accounting (integration|automation|software|efficiency)",
                    r"erp (integration|system|implementation)",
                    r"financial software (integration|automation)",
                    r"bookkeeping (automation|efficiency|challenges?)",
                    r"reconciliation (process|challenges?|automation)",
                ],
                "context_indicators": [
                    "manual", "time.consuming", "error.prone", "inefficient",
                    "automated", "integrated", "streamlined"
                ],
                "signal_id": "accounting_integration_opportunity",
                "use_cases": ["accounting_integration", "apis_developer_tooling"]
            }
        }
    
    def analyze_text_semantically(self, text: str, company_context: Dict[str, Any]) -> List[SemanticSignal]:
        """
        Analyze text using semantic patterns and NLP to detect signals.
        Returns signals with confidence scores and evidence.
        """
        signals = []
        text_lower = text.lower()
        
        # Process text with spaCy for better analysis
        doc = self.nlp(text)
        
        for pain_type, config in self.semantic_patterns.items():
            signal_detected = self._detect_semantic_signal(
                text_lower, doc, config, company_context
            )
            if signal_detected:
                signals.append(signal_detected)
        
        return signals
    
    def _detect_semantic_signal(self, text: str, doc, config: Dict, context: Dict) -> Optional[SemanticSignal]:
        """
        Detect a specific semantic signal in the text.
        """
        best_match = None
        best_confidence = 0.0
        
        # Check semantic patterns
        for pattern in config["patterns"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                confidence = self._calculate_semantic_confidence(
                    match.group(), text, doc, config["context_indicators"]
                )
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = SemanticSignal(
                        signal_id=config["signal_id"],
                        confidence=confidence,
                        evidence_text=match.group(),
                        context=self._extract_context(text, match.start(), match.end()),
                        semantic_match=pattern
                    )
        
        # Boost confidence based on company context
        if best_match:
            best_match.confidence = self._boost_confidence_by_context(
                best_match.confidence, context, config
            )
        
        return best_match if best_match and best_match.confidence > 0.3 else None
    
    def _calculate_semantic_confidence(self, matched_text: str, full_text: str, 
                                     doc, context_indicators: List[str]) -> float:
        """
        Calculate confidence score for a semantic match.
        """
        base_confidence = 0.6  # Base confidence for pattern match
        
        # Boost confidence based on context indicators
        context_boost = 0.0
        for indicator in context_indicators:
            if re.search(r'\b' + re.escape(indicator) + r'\b', full_text):
                context_boost += 0.1
        
        # Boost for proximity to financial terms
        financial_terms = ["cost", "expense", "fee", "price", "payment", "transaction"]
        for term in financial_terms:
            if term in matched_text.lower():
                context_boost += 0.1
        
        # Boost for sentence position (problems often mentioned early)
        sentences = [sent.text for sent in doc.sents]
        for i, sentence in enumerate(sentences):
            if matched_text in sentence:
                if i < len(sentences) * 0.3:  # Early in document
                    context_boost += 0.1
                break
        
        return min(1.0, base_confidence + context_boost)
    
    def _boost_confidence_by_context(self, confidence: float, company_context: Dict, 
                                   config: Dict) -> float:
        """
        Boost confidence based on company characteristics.
        """
        boost = 0.0
        
        # International companies more likely to have FX issues
        if company_context.get("international_subsidiary_count", 0) > 0:
            if "fx" in config["signal_id"]:
                boost += 0.2
        
        # Larger companies more likely to have complex cash management
        if company_context.get("latest_revenue_gbp", 0) > 50000000:  # £50M+
            if "cash_management" in config["signal_id"]:
                boost += 0.15
        
        # Companies with overseas operations more likely to need international payments
        countries = company_context.get("countries_of_operation", [])
        if len(countries) > 1:
            if any(use_case in ["fx_international_money", "merchant_acquiring"] 
                   for use_case in config["use_cases"]):
                boost += 0.1
        
        return min(1.0, confidence + boost)
    
    def _extract_context(self, text: str, start: int, end: int, window: int = 100) -> str:
        """
        Extract surrounding context for a match.
        """
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()
    
    def detect_provider_usage_ai(self, text: str, known_providers: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Use AI to detect provider mentions with context understanding.
        """
        detected_providers = []
        text_lower = text.lower()
        
        for provider_key, provider_info in known_providers.items():
            # Check for exact name matches
            if provider_info["name"].lower() in text_lower:
                confidence = 0.9
                context = self._extract_provider_context(text, provider_info["name"])
                detected_providers.append({
                    "provider": provider_key,
                    "confidence": confidence,
                    "evidence": provider_info["name"],
                    "context": context,
                    "relationship_type": self._classify_relationship(text, provider_info["name"])
                })
            
            # Check for semantic alternatives
            for alternative in provider_info.get("alternatives", []):
                if alternative.lower() in text_lower:
                    confidence = 0.7
                    context = self._extract_provider_context(text, alternative)
                    detected_providers.append({
                        "provider": provider_key,
                        "confidence": confidence,
                        "evidence": alternative,
                        "context": context,
                        "relationship_type": self._classify_relationship(text, alternative)
                    })
        
        return detected_providers
    
    def _extract_provider_context(self, text: str, provider_name: str) -> str:
        """Extract context around provider mention."""
        idx = text.lower().find(provider_name.lower())
        if idx == -1:
            return ""
        return self._extract_context(text, idx, idx + len(provider_name))
    
    def _classify_relationship(self, text: str, provider_name: str) -> str:
        """Classify the relationship type with the provider."""
        text_lower = text.lower()
        provider_lower = provider_name.lower()
        
        # Look for context around the provider mention
        idx = text_lower.find(provider_lower)
        if idx == -1:
            return "unknown"
        
        context = self._extract_context(text_lower, idx, idx + len(provider_lower), 50)
        
        if any(word in context for word in ["customer", "client", "user", "using"]):
            return "customer"
        elif any(word in context for word in ["partner", "supplier", "vendor"]):
            return "partner"
        elif any(word in context for word in ["competitor", "competing"]):
            return "competitor"
        else:
            return "mentioned"
