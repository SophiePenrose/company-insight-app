# Company Insight Screener app

This is a simple Streamlit app for screening UK companies for potential Revolut Business fit.

## What it does

- Upload a CSV of company or accounts-screening results.
- Filter by SIC code, turnover, issue type, issue origin, provider mention, and Revolut-fit score.
- Auto-infer issue buckets and a simple Revolut-fit score from excerpts and provider mentions.
- Export the filtered set to CSV.

## Best input columns

- `company_number`
- `company_name`
- `sic_codes`
- `latest_turnover_gbp`
- `filing_date`
- `issues_found`
- `issue_origin`
- `providers_found`
- `key_updates`
- `excerpts`

## Notes

This is a starter review app, not a final decision engine. It is designed to help shortlist companies and review supporting excerpts.
