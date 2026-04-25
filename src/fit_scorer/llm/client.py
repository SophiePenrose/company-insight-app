import os
from typing import Optional

try:
    import openai
except ImportError:
    openai = None


def llm_json(system: str, user: str, model: Optional[str] = None) -> str:
    if openai is None:
        raise ImportError("OpenAI package is required for LLM calls. Install openai in your environment.")

    model = model or os.environ.get("LLM_MODEL", "gpt-4.1-mini")
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY or LLM_API_KEY must be set for LLM extraction.")

    openai.api_key = api_key
    api_base = os.environ.get("OPENAI_API_BASE")
    if api_base:
        openai.api_base = api_base

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.1,
    )
    return response["choices"][0]["message"]["content"]
