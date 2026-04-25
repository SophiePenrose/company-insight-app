import csv
import argparse
from pathlib import Path
from src.extraction.filing_parser import parse_filing
from src.extraction.base_features import extract_base_features
from src.services.fit_scoring_service import FitScoringService

PIPELINE_VERSION = "v1"


def main(input_csv, output_csv, model_name="gpt-4", prompt_version="v1"):
    scoring_service = FitScoringService(model_name=model_name, prompt_version=prompt_version, pipeline_version=PIPELINE_VERSION)
    with open(input_csv, newline="", encoding="utf-8") as infile, open(output_csv, "w", newline="", encoding="utf-8") as outfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ["fit_score", "fit_score_rationale", "fit_score_evidence", "pipeline_version", "model_name", "prompt_version", "document_hash"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            company_number = row["company_number"]
            filing_id = row.get("filing_id", "")
            filing_type = row.get("filing_type", "")
            filing_date = row.get("filing_date", "")
            source_url = row.get("source_url", "")
            # Parse filing document
            filing_doc = parse_filing(company_number, filing_id, filing_type, filing_date, source_url, pipeline_version=PIPELINE_VERSION)
            # Extract base features
            base_features = extract_base_features(filing_doc)
            # Score
            fit_score_result = scoring_service.score(filing_doc, base_features)
            # Update row
            row["fit_score"] = fit_score_result.scores.get("overall_score")
            row["fit_score_rationale"] = fit_score_result.rationale
            row["fit_score_evidence"] = ", ".join(fit_score_result.evidence.get("excerpts", []))
            row["pipeline_version"] = PIPELINE_VERSION
            row["model_name"] = model_name
            row["prompt_version"] = prompt_version
            row["document_hash"] = fit_score_result.document_hash
            writer.writerow(row)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch score companies using filings and LLM fit scoring.")
    parser.add_argument("input_csv", help="Input CSV with company_number, filing_id, filing_type, filing_date, source_url columns")
    parser.add_argument("output_csv", help="Output CSV for results")
    parser.add_argument("--model", default="gpt-4", help="LLM model name")
    parser.add_argument("--prompt_version", default="v1", help="Prompt version")
    args = parser.parse_args()
    main(args.input_csv, args.output_csv, model_name=args.model, prompt_version=args.prompt_version)
