import json
from typing import List, Dict, Any, Optional

from src.fit_scorer.llm.client import llm_json
from src.fit_scorer.llm.prompts import build_extraction_prompt
from src.fit_scorer.schemas import ExtractionResult


def extract_structured(
    company_name: str,
    documents: List[Dict[str, Any]],
    model: Optional[str] = None,
) -> ExtractionResult:
    document_texts = []
    for doc in documents:
        if not doc.get("downloaded"):
            continue
        text = doc.get("extracted_text", "")
        source = doc.get("filing", {}).get("description", "unknown")
        if text:
            document_texts.append(f"Source: {source}\n{text[:3000]}")

    if not document_texts:
        raise ValueError("No document text available for extraction.")

    prompt = build_extraction_prompt(company_name, document_texts)
    raw = llm_json(
        system="You are an expert financial analyst extracting structured company insights.",
        user=prompt,
        model=model,
    )

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM response was not valid JSON: {exc}\n{raw}")

    return ExtractionResult.parse_obj(payload)
