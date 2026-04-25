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

## LLM Fit Scoring Integration

This project supports advanced fit scoring using a Large Language Model (LLM) such as OpenAI GPT-4 or Gemini.

### How it works

- The scoring pipeline builds a structured prompt from company data and filings.
- If the `OPENAI_API_KEY` environment variable is set, the app will call the LLM API to extract fit signals, segment, use cases, and prohibited industry flags.
- If no API key is set, a stubbed response is used for local development and testing.
- The LLM output is parsed for:
  - Prohibited industry exclusion (hard stop)
  - Segment fit, timing, competitive, and other pillar scores

  - Qualitative severity and evidence trace for each factor

### Setup

1. Obtain an OpenAI API key (or Gemini key, with code adaptation).

2. Set the environment variable in your shell or `.env` file:

   ```sh
   export OPENAI_API_KEY=sk-...
   ```

3. Run the app or scoring script as normal. The LLM will be used automatically if the key is present.

### Testing

- Run `pytest tests/test_gemini_fit.py` to validate prohibited exclusion, fit scoring, and evidence trace logic.
- The tests do not require an API key and use stubbed responses.

### Configuration

- Scoring weights and prohibited industry categories are defined in `src/services/gemini_fit.py`.
- You can tune these as needed for your business logic.

### Example

See `src/services/gemini_fit.py` for a working example and test cases.
