#!/usr/bin/env python3
"""
Daily update script for checking new company filings and updating prospect reports.
Runs daily to identify new group accounts and refresh insights.
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ROOT = Path(__file__).resolve().parents[0]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.clients.companies_house import CompaniesHouseClient
from src.fit_scorer.pipeline import run_company_extraction

def load_latest_baseline() -> Dict[str, Any]:
    """Load the most recent baseline file."""
    output_dir = Path("output")
    baseline_files = list(output_dir.glob("baseline_*.json"))
    if not baseline_files:
        return {"results": []}

    latest = max(baseline_files, key=lambda p: p.stat().st_mtime)
    with latest.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_existing_reports() -> Dict[str, Dict[str, Any]]:
    """Load existing reports indexed by company number."""
    reports_file = Path("output") / "prospect_reports.jsonl"
    reports = {}

    if not reports_file.exists():
        return reports

    with reports_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                report = json.loads(line)
                company_number = report.get("company_number")
                if company_number:
                    reports[company_number] = report

    return reports

def check_for_new_filings(ch_client: CompaniesHouseClient, company_number: str, last_check_date: str) -> List[Dict[str, Any]]:
    """Check if there are new filings since last check."""
    try:
        history = ch_client.filing_history(company_number, items_per_page=50)
        items = history.get("items", [])

        new_filings = []
        for item in items:
            filing_date = item.get("date")
            if filing_date and filing_date > last_check_date:
                # Check if it's a group accounts filing
                description = item.get("description", "").lower()
                if any(keyword in description for keyword in ["group accounts", "annual report", "accounts with group"]):
                    new_filings.append(item)

        return new_filings
    except Exception as e:
        print(f"Error checking filings for {company_number}: {e}")
        return []

def update_company_report(ch_client: CompaniesHouseClient, company: Dict[str, Any], existing_report: Dict[str, Any] = None) -> Dict[str, Any]:
    """Update or create report for a company."""
    company_number = company["company_number"]
    company_name = company["company_name"]

    print(f"Updating {company_name} ({company_number})")

    try:
        # Get fresh profile
        profile = ch_client.company_profile(company_number)

        # Run full extraction
        extraction_result = run_company_extraction(
            ch_client=ch_client,
            company_number=company_number,
            company_name=company_name,
            company_profile=profile,
            max_docs=2,
            model="gpt-4o-mini" if os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY") else None,
        )

        report = extraction_result.get("report")
        if report:
            report["updated_at"] = datetime.utcnow().isoformat() + "Z"
            report["update_reason"] = "daily_refresh"

        return report

    except Exception as e:
        print(f"Error updating {company_name}: {e}")
        return None

def main():
    # Load API keys
    api_key = os.getenv("COMPANIES_HOUSE_API_KEY")
    llm_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")

    if not api_key:
        print("Error: COMPANIES_HOUSE_API_KEY not found in .env")
        sys.exit(1)

    if not llm_key:
        print("Warning: LLM API key not found. Schema extraction will be skipped.")

    # Load baseline data
    baseline = load_latest_baseline()
    companies = baseline.get("results", [])
    print(f"Loaded {len(companies)} companies from baseline")

    # Load existing reports
    existing_reports = load_existing_reports()
    print(f"Loaded {len(existing_reports)} existing reports")

    error_log = []

    # Initialize client
    ch_client = CompaniesHouseClient(api_key)

    # Determine last check date (use yesterday as cutoff)
    last_check_date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Check for updates
    updates_needed = []
    new_filings_found = []

    for company in companies:
        company_number = company.get("company_number")
        if not company_number:
            continue

        try:
            existing_report = existing_reports.get(company_number)
            if existing_report:
                # Check for new filings
                new_filings = check_for_new_filings(ch_client, company_number, last_check_date)
                if new_filings:
                    print(f"New filings found for {company.get('company_name')}: {len(new_filings)}")
                    new_filings_found.extend(new_filings)
                    updates_needed.append(company)
            else:
                # No existing report, need to create one
                updates_needed.append(company)
        except Exception as e:
            error_msg = f"Error processing company {company.get('company_name')} ({company_number}): {e}"
            print(error_msg)
            error_log.append(error_msg)

    # Also refresh all reports periodically (e.g., weekly)
    # For now, just update companies with new filings or no report

    if not updates_needed:
        print("No updates needed today.")
        return

    print(f"Updating {len(updates_needed)} companies...")

    # Update reports
    updated_reports = []
    reports_file = Path("output") / "prospect_reports.jsonl"

    for company in updates_needed:
        try:
            report = update_company_report(ch_client, company, existing_reports.get(company["company_number"]))
            if report:
                updated_reports.append(report)
                # Append to reports file
                with reports_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(report) + "\n")
        except Exception as e:
            error_msg = f"Error updating report for {company.get('company_name')} ({company.get('company_number')}): {e}"
            print(error_msg)
            error_log.append(error_msg)

    # Save update summary
    update_file = Path("output") / f"daily_update_{datetime.now().strftime('%Y%m%d')}.json"
    with update_file.open("w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "update_date": datetime.utcnow().isoformat() + "Z",
                "companies_checked": len(companies),
                "updates_needed": len(updates_needed),
                "reports_updated": len(updated_reports),
                "new_filings_found": len(new_filings_found),
                "errors": len(error_log),
            },
            "updated_reports": [r["report_id"] for r in updated_reports if r],
            "errors": error_log,
        }, f, indent=2)

    print(f"Daily update complete! Updated {len(updated_reports)} reports.")
    print(f"Summary saved to: {update_file}")
    if error_log:
        print(f"Encountered {len(error_log)} errors. See summary file for details.")

if __name__ == "__main__":
    main()