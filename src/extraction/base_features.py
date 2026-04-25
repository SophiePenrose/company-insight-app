import re
from typing import List, Dict, Any
from .filing_parser import FilingDocument

# Example keyword lists and regex patterns (customize for your use case)
ISSUE_KEYWORDS = ["loss", "fraud", "insolvency", "liquidation", "warning", "risk"]
PROVIDER_KEYWORDS = ["Revolut", "Barclays", "HSBC", "Wise", "Starling"]
UPDATE_PATTERNS = [r"change of (address|director|officer)", r"appointment of (director|auditor)"]


def extract_issues_found(text: str) -> List[str]:
    found = []
    for kw in ISSUE_KEYWORDS:
        if re.search(rf"\\b{re.escape(kw)}\\b", text, re.IGNORECASE):
            found.append(kw)
    return found

def extract_providers_found(text: str) -> List[str]:
    found = []
    for kw in PROVIDER_KEYWORDS:
        if re.search(rf"\\b{re.escape(kw)}\\b", text, re.IGNORECASE):
            found.append(kw)
    return found

def extract_key_updates(text: str) -> List[str]:
    found = []
    for pat in UPDATE_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            found.append(m.group(0))
    return found

def extract_excerpts(text: str, n=3) -> List[str]:
    # Return n most relevant sentences (simple heuristic)
    sentences = re.split(r"(?<=[.!?]) +", text)
    return sentences[:n]

def extract_base_features(filing: FilingDocument) -> Dict[str, Any]:
    all_text = " ".join([p.text for p in filing.pages])
    issues_found = extract_issues_found(all_text)
    providers_found = extract_providers_found(all_text)
    key_updates = extract_key_updates(all_text)
    excerpts = extract_excerpts(all_text)
    # Issue origin: simple heuristic (could be improved)
    issue_origin = "filing" if issues_found else "none"
    return {
        "issues_found": issues_found,
        "issue_origin": issue_origin,
        "providers_found": providers_found,
        "key_updates": key_updates,
        "excerpts": excerpts,
    }
