from typing import List


def build_extraction_prompt(company_name: str, document_texts: List[str]) -> str:
    prompt = [
        f"You are an expert financial research assistant. Extract structured company insights from company filing text.",
        f"Company name: {company_name}",
        "Produce only valid JSON that matches the schema exactly.",
        "If information is missing, set the field value to null and confidence to 'low'.",
        "Do not hallucinate providers or insights.",
        "Include evidence quotes and their source for every field.",
        "",
        "Schema:",
        "{\n"
        "  \"company_name\": {\"value\": string|null, \"confidence\": \"high|medium|low\", \"evidence\": [{\"quote\": string, \"source\": string, \"url\": string|null}]},\n"
        "  \"turnover_gbp\": {\"value\": string|null, \"confidence\": \"high|medium|low\", \"evidence\": [...]},\n"
        "  \"employees\": {\"value\": string|null, \"confidence\": \"high|medium|low\", \"evidence\": [...]},\n"
        "  \"industry\": {\"value\": string|null, \"confidence\": \"high|medium|low\", \"evidence\": [...]},\n"
        "  \"business_model\": {\"value\": string|null, \"confidence\": \"high|medium|low\", \"evidence\": [...]},\n"
        "  \"geos\": {\"value\": string|null, \"confidence\": \"high|medium|low\", \"evidence\": [...]},\n"
        "  \"fx_intensity\": {\"value\": string|null, \"confidence\": \"high|medium|low\", \"evidence\": [...]},\n"
        "  \"payments_acceptance\": {\"value\": string|null, \"confidence\": \"high|medium|low\", \"evidence\": [...]},\n"
        "  \"spend_profile\": {\"value\": string|null, \"confidence\": \"high|medium|low\", \"evidence\": [...]},\n"
        "  \"ap_payroll_complexity\": {\"value\": string|null, \"confidence\": \"high|medium|low\", \"evidence\": [...]},\n"
        "  \"tech_stack\": {\"value\": string|null, \"confidence\": \"high|medium|low\", \"evidence\": [...]},\n"
        "  \"triggers\": {\"value\": string|null, \"confidence\": \"high|medium|low\", \"evidence\": [...]},\n"
        "  \"rarer_insights\": [{\"type\": \"goal|cost|risk|policy|working_capital\", \"insight\": string, \"strength_1_to_5\": integer, \"evidence\": {\"quote\": string, \"source\": string, \"url\": string|null}}],\n"
        "  \"providers\": [{\"provider\": string, \"category\": \"bank|psp|ecom|erp|expenses|payroll_eor|treasury\", \"detected_as\": \"explicit|inferred\", \"confidence\": \"high|medium|low\", \"evidence\": [{\"quote\": string, \"source\": string, \"url\": string|null}]}]\n"
        "}"
    ]

    documents_prompt = []
    for index, text in enumerate(document_texts, start=1):
        documents_prompt.append(f"Document {index}:\n{text[:3000]}")

    prompt.extend([
        "",
        "Extract from the following document text:",
        *documents_prompt,
        "",
        "Return only the JSON object.",
    ])

    return "\n".join(prompt)
