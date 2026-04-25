from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List
import logging
from src.extraction.filing_parser import FilingDocument
from src.extraction.base_features import extract_base_features
from src.services.gemini_fit import build_gemini_prompt, call_llm_api, parse_gemini_response, calculate_overall_fit_score
import os
import json

logger = logging.getLogger("fit_scoring_service")

@dataclass
class FitScoreResult:
    scores: Dict[str, Any]
    rationale: str
    evidence: Dict[str, Any]
    model_name: str
    prompt_version: str
    document_hash: str
    pipeline_version: str
    raw_llm_output: Dict[str, Any] = field(default_factory=dict)

    def to_json(self):
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

class FitScoringService:
    def __init__(self, model_name: str = "gpt-4", prompt_version: str = "v1", pipeline_version: str = "v1"):
        self.model_name = model_name
        self.prompt_version = prompt_version
        self.pipeline_version = pipeline_version
        self.api_key = os.getenv("OPENAI_API_KEY")

    def score(self, filing_doc: FilingDocument, base_features: Dict[str, Any], top_k: int = 3) -> FitScoreResult:
        # Select top-K evidence snippets per matrix dimension
        evidence_snippets = base_features.get("excerpts", [])[:top_k]
        prompt = build_gemini_prompt({
            **base_features,
            "company_number": filing_doc.company_number,
            "filing_id": filing_doc.filing_id,
            "filing_type": filing_doc.filing_type,
            "filing_date": filing_doc.filing_date,
            "document_hash": filing_doc.document_hash,
            "pipeline_version": self.pipeline_version,
        }, filing_text=" ".join([p.text for p in filing_doc.pages]))
        llm_response = call_llm_api(prompt, api_key=self.api_key, model=self.model_name)
        llm_result = parse_gemini_response(llm_response)
        scores = calculate_overall_fit_score(llm_result)
        rationale = llm_result.get("prohibited_reason", "") or llm_result.get("segment_fit", {}).get("confidence", "")
        return FitScoreResult(
            scores=scores,
            rationale=rationale,
            evidence={"excerpts": evidence_snippets},
            model_name=self.model_name,
            prompt_version=self.prompt_version,
            document_hash=filing_doc.document_hash,
            pipeline_version=self.pipeline_version,
            raw_llm_output=llm_result
        )
