import os
import requests
import json
import yaml
import logging
import sys
# Configure structured logging (JSON format)
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'level': record.levelname,
            'time': self.formatTime(record, self.datefmt),
            'message': record.getMessage(),
            'name': record.name,
        }
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

logger = logging.getLogger("fit_scoring")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    logger.addHandler(handler)

def call_llm_api(prompt: str, api_key: str = None, model: str = "gpt-4") -> str:
    """
    Call the LLM API (OpenAI or Gemini) with the given prompt and return the response text.
    If api_key is None, will raise an error.
    """
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("No LLM API key provided. Set OPENAI_API_KEY in your environment.")
        raise RuntimeError("No LLM API key provided. Set OPENAI_API_KEY in your environment.")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 2048
    }
    logger.info(f"Calling LLM API: model={model}")
    response = requests.post(url, headers=headers, json=data, timeout=60)
    response.raise_for_status()
    logger.info("LLM API call successful.")
    return response.json()["choices"][0]["message"]["content"]

# Stub for Gemini or LLM integration
# Replace with actual Gemini API endpoint and authentication as needed
def get_gemini_fit_score(company_data: dict, filing_text: str = "") -> int:
    """
    Call Gemini (or other LLM) to get a fit score for the company.
    Returns an integer score between 0 and 100, or 0 if prohibited.
    """
    prompt = build_gemini_prompt(company_data, filing_text)
    api_key = os.getenv("OPENAI_API_KEY")
    use_llm = bool(api_key)
    logger.info(f"Scoring company: {company_data.get('name', 'unknown')}")
    if use_llm:
        try:
            llm_response = call_llm_api(prompt, api_key=api_key)
            gemini_result = parse_gemini_response(llm_response)
        except Exception as e:
            logger.error(f"LLM API error: {e}. Falling back to stub response.")
            use_llm = False
    if not use_llm:
        stub_response = '''{
  "prohibited": false,
  "segment_fit": {"score": 31, "why_we_win": 12, "green_flags": 12, "red_flags": 3, "confidence": "evidence"},
  "timing_modifier": {"score": 5, "reason": "expansion and cost optimisation", "confidence": "evidence"},
  "competitive_modifier": {"score": 5, "reason": "incumbent bank + FX risk language", "confidence": "evidence"},
  "other_pillars": {"payments": 8, "fx": 9, "expenses": 6, "billpay": 5, "confidence": "proxy"}
}'''
        gemini_result = parse_gemini_response(stub_response)
    if is_prohibited_company(gemini_result):
        logger.warning(f"Prohibited industry: {gemini_result.get('prohibited_reason', 'See LLM output')}")
        return 0
    fit = calculate_overall_fit_score(gemini_result)
    logger.info(f"Fit score for {company_data.get('name', 'unknown')}: {fit['overall_score']}")
    return fit["overall_score"]

# ---
# Prospect Fit Scoring Framework (OSINT-Only, Auditable)
#
# Each indicator is scored based on:
#   - Strength of evidence: none / weak / strong (0, 0.5, 1)
#   - Source confidence: group accounts/filings (1.0), website/LinkedIn (0.8), news (0.7), job posts (0.6)
#   - Multiple sources can reinforce a score, but max per indicator is capped at 1.0
#   - Negative adjustments are cumulative but capped (e.g., -20 max)
#   - All scores are traceable to their evidence and source for auditability
#
# Example usage:
#   evidence = {
#       'fx_exposure': [
#           ('strong', 1.0, 'Group accounts: FX risk, multi-currency revenue'),
#           ('weak', 0.8, 'Website: "global customers"'),
#       ],
#       ...
#   }
#   score, evidence_used = score_indicator(evidence['fx_exposure'], 20)
#
def score_indicator(evidence_list, weight):
    """
    evidence_list: list of (strength, confidence, evidence_string)
        - strength: float in [0, 1] (e.g. 0.0 = none, 0.5 = weak, 1.0 = strong, or any value in between)
        - confidence: float in [0, 1] (source reliability)
        - evidence_string: description
    weight: max points for this indicator
    Returns (score, best_evidence_string)
    """
    max_score = 0
    best_evidence = None
    for strength, confidence, evidence in evidence_list:
        # Accept float strengths (0.0–1.0)
        try:
            rubric = float(strength)
        except (ValueError, TypeError):
            rubric = {"none": 0, "weak": 0.5, "strong": 1}.get(str(strength).lower(), 0)
        score = rubric * confidence * weight
        if score > max_score:
            max_score = score
            best_evidence = evidence
    return max_score, best_evidence


def load_scoring_weights(config_path="config/scoring_weights.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def get_scoring_weights():
    # Cache weights after first load
    if not hasattr(get_scoring_weights, "_weights"):
        get_scoring_weights._weights = load_scoring_weights()
    return get_scoring_weights._weights


def load_negative_weights(config_path="config/negative_weights.yaml"):
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
        return data.get("negative_weights", {})

def get_negative_weights():
    if not hasattr(get_negative_weights, "_weights"):
        get_negative_weights._weights = load_negative_weights()
    return get_negative_weights._weights

def compute_osint_fit_score(evidence_dict):
    """
    evidence_dict: {indicator: list of (strength, confidence, evidence_string)}
    Returns: (score, evidence_trace, profile_completeness)
    """
    scoring_weights = get_scoring_weights()
    negative_weights = get_negative_weights()
    score = 0
    evidence_trace = {}
    filled_indicators = 0
    total_indicators = len(scoring_weights) + len(negative_weights)
    logger.info(f"Computing OSINT fit score. Indicators: {list(scoring_weights.keys()) + list(negative_weights.keys())}")
    # Positive indicators
    for k, w in scoring_weights.items():
        ev_list = evidence_dict.get(k, [])
        if ev_list:
            filled_indicators += 1
        pts, ev = score_indicator(ev_list, w)
        score += pts
        if ev:
            evidence_trace[k] = ev
    # Negative indicators (cumulative, capped)
    neg_total = 0
    for k, w in negative_weights.items():
        ev_list = evidence_dict.get(k, [])
        if ev_list:
            filled_indicators += 1
        pts, ev = score_indicator(ev_list, abs(w))
        neg = -pts if pts > 0 else 0
        neg_total += neg
        if ev:
            evidence_trace[k] = ev
    neg_total = max(neg_total, -20)  # Cap total negative adjustment
    score += neg_total
    score = max(0, min(score, 100))
    profile_completeness = filled_indicators / total_indicators if total_indicators > 0 else 1.0
    logger.info(f"OSINT fit score: {score}, completeness: {profile_completeness:.2f}")
    return score, evidence_trace, profile_completeness

# ---
# Update: Gemini/LLM prompt now requests holistic, qualitative severity scoring for relevant factors (e.g., FX pain, cost pressure, market volatility).
def load_prohibited_industries(config_path="config/prohibited_industries.yaml"):
     with open(config_path, "r") as f:
          data = yaml.safe_load(f)
          return data.get("prohibited_industries", [])

def get_prohibited_list():
     if not hasattr(get_prohibited_list, "_list"):
          get_prohibited_list._list = load_prohibited_industries()
     return get_prohibited_list._list

def build_gemini_prompt(company_data: dict, filing_text: str = "") -> str:
     """
     Build a structured prompt for Gemini/LLM to extract and score fit features, segment, use cases, and GP levers.
     Now requests severity scoring (0–1) for relevant factors using holistic, qualitative judgment.
     """
     prohibited_list = get_prohibited_list()
     prohibited_str = "\n".join(f"- {item}" for item in prohibited_list)
     prompt = f'''
Before scoring, check if the company’s industry or business activity matches any of the following prohibited categories. If so, set "prohibited": true in your output, and provide the evidence and source. If not, set "prohibited": false.

Prohibited Nature of Business – UK Revolut Business:
{prohibited_str}

Given the following company group filing text and structured data, extract and score the following for Revolut Business prospecting:

1. Segment Fit (0–40):
    - Why we win alignment (0–15)
    - Green flags (0–15)
    - Red flags (0–10, subtract only if evidence exists, cap at 10)
2. Timing/Trigger modifier (−10 to +10): 
    - Expansion, replatform, FX volatility, cost optimisation, leadership change, blockers
3. Competitive/Stack modifier (−10 to +10): 
    - Incumbent stack, pains, best-in-class/no window
4. Other Pillars (0–40): 
    - Payments need (0–10)
    - FX intensity (0–10)
    - Spend control & Expenses (0–10)
    - AP/BillPay depth (0–10)
5. For each, specify if evidence is direct, inferred, or unknown.

For the following factors, rate the severity on a scale from 0 (none) to 1 (extreme), using your best judgment based on the evidence provided. Consider the context, trends, and language used. Output both the score and a brief justification for each:
- FX pain or exposure
- Cost/margin pressure
- Market volatility (especially for relevant currency pairs)
- Working capital strain
- Any other major pain points or triggers

For currency pairs and market volatility, explicitly:
- List the specific currency pairs mentioned or implied (e.g., EUR/GBP, USD/JPY)
- State the evidence and its source (e.g., group accounts, filings, website, news, job ads)
- Indicate if recent market trends or volatility are mentioned or can be inferred, and how they impact the company
- Provide a severity score (0–1) and a justification for each

Additionally, assign the company to one or more of the following UK mid-market segments and use cases. For each, provide evidence and confidence (direct/inferred/unknown):

Segments: International e-commerce, Travel, Tech/SaaS, Advertising/Marketing, Consulting/Professional Services, Retail/Wholesale/Manufacturing, Real Estate, Single-market, Cash-heavy, Logistics/Services

Use Cases: FX/cross-border, Multi-currency, Cards/Expenses, Savings, Acquiring

For each, note any GP levers present (multi-currency accounts, card volume, expense management, savings, acquiring) and any relevant benchmarks.

Return a JSON object:
{{
  "prohibited": bool,
  "prohibited_reason": str,
  "prohibited_source": str,
  "segment_fit": {{"score": int, "why_we_win": int, "green_flags": int, "red_flags": int, "confidence": str}},
  "timing_modifier": {{"score": int, "reason": str, "confidence": str}},
  "competitive_modifier": {{"score": int, "reason": str, "confidence": str}},
  "other_pillars": {{"payments": int, "fx": int, "expenses": int, "billpay": int, "confidence": str}},
  "severity": {{
     "fx_pain": {{"strength": float, "justification": str}},
     "cost_pressure": {{"strength": float, "justification": str}},
     "market_volatility": {{"strength": float, "justification": str}},
     "working_capital_strain": {{"strength": float, "justification": str}},
     "currency_pairs": {{"strength": float, "justification": str}}
  }},
  "segment": {{"name": str, "confidence": str, "evidence": str}},
  "use_cases": [{{"name": str, "confidence": str, "evidence": str}}],
  "gp_levers": [str],
  "benchmarks": {{"monthly_gp_mab": float, "gp_multiplier": float}}
}}

Company Data: {json.dumps(company_data, indent=2)}

Filing Text: {filing_text[:4000]}  # Truncate for prompt size
'''
     return prompt

def parse_gemini_response(response_text: str) -> dict:
    """
    Parse the LLM's JSON response and handle errors.
    """
    try:
        # Find the first JSON object in the response
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        json_str = response_text[start:end]
        return json.loads(json_str)
    except Exception as e:
        return {"error": f"Failed to parse Gemini response: {e}", "raw": response_text}

def calculate_overall_fit_score(gemini_result: dict) -> dict:
    """
    Calculate the overall prospect priority score from Gemini/LLM output.
    Returns a dict with score, breakdown, and confidence.
    """
    # Defaults for missing data
    seg = gemini_result.get("segment_fit", {})
    why = seg.get("why_we_win", 0)
    green = seg.get("green_flags", 0)
    red = seg.get("red_flags", 0)
    seg_score = why + green + (10 - min(red, 10))
    seg_score = max(0, min(seg_score, 40))

    timing = gemini_result.get("timing_modifier", {}).get("score", 0)
    timing = max(-10, min(timing, 10))

    comp = gemini_result.get("competitive_modifier", {}).get("score", 0)
    comp = max(-10, min(comp, 10))

    pillars = gemini_result.get("other_pillars", {})
    payments = pillars.get("payments", 0)
    fx = pillars.get("fx", 0)
    expenses = pillars.get("expenses", 0)
    billpay = pillars.get("billpay", 0)
    other_total = sum([payments, fx, expenses, billpay])
    other_total = max(0, min(other_total, 40))

    overall = seg_score + other_total + timing + comp
    overall = max(0, min(overall, 100))

    return {
        "overall_score": overall,
        "segment_fit": seg_score,
        "other_pillars": other_total,
        "timing_modifier": timing,
        "competitive_modifier": comp,
        "confidence": seg.get("confidence", "unknown"),
        "breakdown": {
            "why_we_win": why,
            "green_flags": green,
            "red_flags": red,
            "payments": payments,
            "fx": fx,
            "expenses": expenses,
            "billpay": billpay
        },
        "raw": gemini_result
    }

def extract_segment_and_use_case_info(gemini_result: dict) -> dict:
    """
    Extract segment, use case, and GP lever info from Gemini/LLM output for reporting or advanced scoring.
    """
    segment = gemini_result.get("segment", {})
    use_cases = gemini_result.get("use_cases", [])
    gp_levers = gemini_result.get("gp_levers", [])
    benchmarks = gemini_result.get("benchmarks", {})
    return {
        "segment": segment,
        "use_cases": use_cases,
        "gp_levers": gp_levers,
        "benchmarks": benchmarks
    }

# --- Example: Parsing and using severity scores from Gemini/LLM output in the scoring pipeline

def extract_severity_scores(gemini_result):
    """
    Extracts severity scores from Gemini/LLM output and maps them to evidence for scoring.
    Returns a dict suitable for compute_osint_fit_score.
    """
    severity = gemini_result.get("severity", {})
    evidence = {}
    if "fx_pain" in severity:
        s = severity["fx_pain"].get("strength", 0)
        j = severity["fx_pain"].get("justification", "")
        evidence["fx_exposure"] = [(s, 1.0, j)]
    if "cost_pressure" in severity:
        s = severity["cost_pressure"].get("strength", 0)
        j = severity["cost_pressure"].get("justification", "")
        evidence["cost_pressure"] = [(s, 1.0, j)]
    if "market_volatility" in severity:
        s = severity["market_volatility"].get("strength", 0)
        j = severity["market_volatility"].get("justification", "")
        evidence["market_volatility"] = [(s, 1.0, j)]
    if "working_capital_strain" in severity:
        s = severity["working_capital_strain"].get("strength", 0)
        j = severity["working_capital_strain"].get("justification", "")
        evidence["working_capital_strain"] = [(s, 1.0, j)]
    # New: currency_pairs (if present in LLM output)
    if "currency_pairs" in severity:
        s = severity["currency_pairs"].get("strength", 0)
        j = severity["currency_pairs"].get("justification", "")
        evidence["currency_pairs"] = [(s, 1.0, j)]
    return evidence

def is_prohibited_company(gemini_result: dict) -> bool:
    """
    Returns True if the company is prohibited, based on LLM output.
    """
    return gemini_result.get("prohibited", False)

# --- Example usage of the OSINT fit scoring framework (non-prohibited company) ---
if __name__ == "__main__":
    # Example evidence for a hypothetical company
    evidence = {
        "fx_exposure": [
            (0.9, 1.0, "2025 group accounts: explicit FX risk, multi-currency revenue streams, major EUR/GBP swing"),
            (0.5, 0.8, "Website: 'global customers in 12 countries'"),
        ],
        "product_wedge": [
            (0.8, 0.8, "Website: 'online payments, e-commerce, card acceptance'"),
        ],
        "delegation_complexity": [
            (0.5, 0.8, "LinkedIn: hiring for 'Finance Operations Manager'"),
        ],
        "card_spend_model": [
            (0.0, 0.8, "No evidence found in filings or website"),
        ],
        "multi_entity": [
            (1.0, 1.0, "Companies House: 3 active subsidiaries in UK/EU"),
        ],
        "expansion_trigger": [
            (1.0, 0.7, "Press release: opening new office in Germany"),
        ],
        "leadership_change": [
            (0.5, 0.8, "LinkedIn: new CFO joined 3 months ago"),
        ],
        "cost_pressure": [
            (1.0, 1.0, "2025 group accounts: 'margin pressure from payment processing fees'"),
        ],
        "stakeholders_identifiable": [
            (1.0, 0.8, "LinkedIn: CFO and Head of Procurement both listed"),
        ],
        "evidence_pain_solution": [
            (1.0, 0.8, "Job ad: 'implementing new expense management system'"),
        ],
        # Negative indicators
        "inertia": [
            (0.5, 0.7, "News: 'longstanding relationship with incumbent bank'"),
        ],
        "trust_hurdle": [
            (0.0, 1.0, "No evidence of risk-averse posture"),
        ],
    }
    score, evidence_trace, profile_completeness = compute_osint_fit_score(evidence)
    print(f"Prospect Fit Score: {score}")
    print(f"Profile completeness: {profile_completeness:.0%}")
    print("Evidence Trace:")
    for k, v in evidence_trace.items():
        print(f"  {k}: {v}")

# --- Example: YAML-based thresholds loading, tier assignment, and ranking logic for company scores ---

def load_score_thresholds(config_path="config/score_thresholds.yaml"):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)["tiers"]

def assign_tier(score, thresholds):
    if score >= thresholds["tier_1"]:
        return "Tier 1"
    elif score >= thresholds["tier_2"]:
        return "Tier 2"
    elif score >= thresholds["tier_3"]:
        return "Tier 3"
    else:
        return "Watchlist"

def rank_and_tier_companies(company_scores, thresholds):
    # company_scores: list of dicts with at least {"company_name", "score"}
    sorted_companies = sorted(company_scores, key=lambda x: x["score"], reverse=True)
    for i, c in enumerate(sorted_companies, 1):
        c["rank"] = i
        c["tier"] = assign_tier(c["score"], thresholds)
    return sorted_companies
