#!/usr/bin/env python3
"""
Batch analysis script for prospecting companies from CSV.
Loads companies from CSV, runs full analysis pipeline, and saves structured reports.
"""


import os
import json
import sys
import logging
import yaml
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Structured logging setup
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

logger = logging.getLogger("batch_scoring")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    logger.addHandler(handler)

load_dotenv()

ROOT = Path(__file__).resolve().parents[0]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from src.clients.companies_house import CompaniesHouseClient
from src.fit_scorer.pipeline import run_company_extraction
from src.services.gemini_fit import load_score_thresholds, rank_and_tier_companies

def load_companies_from_csv(csv_path: str):
    companies = []
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith("company_name") and "company_number" in line.lower():
                continue
            if "," not in line:
                continue
            company_name, company_number = line.rsplit(",", 1)
            companies.append({
                "company_name": company_name.strip(),
                "company_number": company_number.strip(),
            })
    return companies

def main():
    # Configuration
    csv_path = "company_numbers.csv"  # Default, can be overridden
    max_companies = None
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            max_companies = int(sys.argv[2])
        except ValueError:
            print("Warning: second argument must be an integer for max companies. Ignoring.")

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    reports_file = output_dir / "prospect_reports.jsonl"
    baseline_file = output_dir / f"baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # Load API keys
    api_key = os.getenv("COMPANIES_HOUSE_API_KEY")
    llm_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")

    if not api_key:
        print("Error: COMPANIES_HOUSE_API_KEY not found in .env")
        sys.exit(1)

    if not llm_key:
        print("Warning: LLM API key not found. Schema extraction will be skipped.")


    # Load companies
    try:
        companies = load_companies_from_csv(csv_path)
        logger.info(f"Loaded {len(companies)} companies from {csv_path}")
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        sys.exit(1)

    # Initialize client
    ch_client = CompaniesHouseClient(api_key)

    # Run analysis
    results = []

    logger.info("Starting batch analysis...")


    for i, company in enumerate(companies):
        company_number = company.get("company_number", "").strip()
        company_name = company.get("company_name", "").strip()

        if not company_number or not company_name:
            logger.warning(f"Skipping invalid company {i+1}: missing number or name")
            continue

        logger.info(f"Analyzing {i+1}/{len(companies)}: {company_name} ({company_number})")

        try:
            # Get company profile
            profile = ch_client.company_profile(company_number)

            # Run full extraction pipeline
            extraction_result = run_company_extraction(
                ch_client=ch_client,
                company_number=company_number,
                company_name=company_name,
                company_profile=profile,
                max_docs=2,
                model="gpt-4o-mini" if llm_key else None,
            )

            result = {
                "company_number": company_number,
                "company_name": company_name,
                "profile": profile,
                "extraction": extraction_result.get("extraction"),
                "scoring": extraction_result.get("scoring"),
                "extraction_error": extraction_result.get("extraction_error"),
                "report": extraction_result.get("report"),
                "analyzed_at": datetime.utcnow().isoformat() + "Z",
            }
            results.append(result)

            # Save individual report
            if result.get("report"):
                with reports_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(result["report"]) + "\n")

        except Exception as e:
            logger.error(f"Error analyzing {company_name}: {e}")
            results.append({
                "company_number": company_number,
                "company_name": company_name,
                "error": str(e),
                "analyzed_at": datetime.utcnow().isoformat() + "Z",
            })


    # Rank and tier companies using config thresholds
    thresholds = load_score_thresholds()
    # Only include results with a valid score
    scored_results = [r for r in results if r.get("scoring") and r["scoring"].get("score") is not None]
    for r in scored_results:
        r["score"] = r["scoring"]["score"]
        r["company_name"] = r.get("company_name")
    ranked = rank_and_tier_companies(scored_results, thresholds)
    # Update results with rank/tier
    rank_map = {r["company_number"]: {"rank": r["rank"], "tier": r["tier"]} for r in ranked}
    for r in results:
        if r.get("company_number") in rank_map:
            r["rank"] = rank_map[r["company_number"]]["rank"]
            r["tier"] = rank_map[r["company_number"]]["tier"]

    # Save baseline results
    with baseline_file.open("w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "csv_source": csv_path,
                "companies_analyzed": len(results),
                "llm_used": bool(llm_key),
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
            "results": results,
        }, f, indent=2)

    logger.info(f"Batch analysis complete!")
    logger.info(f"Results saved to: {baseline_file}")
    logger.info(f"Reports appended to: {reports_file}")

    # Summary
    valid_results = [r for r in results if "error" not in r]
    if valid_results:
        scores = [r.get("scoring", {}).get("score", 0) for r in valid_results if r.get("scoring")]
        if scores:
            avg_score = sum(scores) / len(scores)
            logger.info(f"Average score: {avg_score:.1f}")
            tier_counts = {}
            for r in valid_results:
                tier = r.get("tier", "unknown")
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
            logger.info(f"Priority tiers: {tier_counts}")

if __name__ == "__main__":
    main()