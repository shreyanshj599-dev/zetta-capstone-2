"""Groq provider — uses the OpenAI-compatible SDK pointed at api.groq.com.

This is the Adapter pattern (Bucket 1): we wrap the OpenAI SDK behind our
domain interface (`LLMProvider`) so callers see only `extract_company_facts`,
not OpenAI-shaped APIs.
"""

import json
import logging

from openai import OpenAI
from pydantic import ValidationError

from app.core.config import get_settings
from app.schemas.company import CompanyFacts
from app.services.llm.base import LLMError
from app.services.scraper import FetchedPage

log = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

SYSTEM_PROMPT = """You are a company-facts extractor. You read scraped text from a company's website and return a single JSON object that matches the provided schema exactly.

Rules:
- Output JSON only. No prose, no markdown, no code fences.
- If you are unsure of a field, infer the most likely value but lower `confidence`.
- `industry` MUST be one of: saas, fintech, healthcare, ecommerce, hardware, consulting, other.
- `size_bucket` MUST be one of: 1-10, 11-50, 51-200, 201-1000, 1000+.
- `icp_fit_score` is 0-100; 100 = ideal customer profile match for an MLOps/dev-tools sale.
- `confidence` is 0-1; reflect how clear the source text was.
"""


def _build_user_prompt(domain: str, pages: list[FetchedPage]) -> str:
    schema = json.dumps(CompanyFacts.model_json_schema(), indent=2)
    parts = [f"Domain: {domain}", "", "JSON schema the response MUST satisfy:", schema, ""]
    parts.append("Scraped pages (truncated):")
    for p in pages:
        parts.append(f"\n--- {p.url} ---\n{p.text}")
    return "\n".join(parts)


class GroqProvider:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.groq_api_key:
            raise LLMError("GROQ_API_KEY is not set")
        self._client = OpenAI(api_key=settings.groq_api_key, base_url=GROQ_BASE_URL)
        self._model = settings.groq_model

    def extract_company_facts(self, domain: str, pages: list[FetchedPage]) -> CompanyFacts:
        if not pages:
            raise LLMError(f"No pages were scraped for {domain}; cannot extract facts")

        user_prompt = _build_user_prompt(domain, pages)
        last_error: str | None = None

        for attempt in (1, 2):
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
            if last_error is not None:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Your previous response failed validation:\n{last_error}\n"
                            "Return corrected JSON that exactly matches the schema."
                        ),
                    }
                )

            log.info("groq_call domain=%s attempt=%d model=%s", domain, attempt, self._model)
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=messages,  # type: ignore[arg-type]
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=1024,
            )
            raw = resp.choices[0].message.content or ""

            try:
                parsed = json.loads(raw)
                facts = CompanyFacts.model_validate(parsed)
                log.info("groq_call_ok domain=%s confidence=%.2f", domain, facts.confidence)
                return facts
            except (json.JSONDecodeError, ValidationError) as e:
                last_error = str(e)[:500]
                log.warning("groq_validation_failed domain=%s attempt=%d err=%s",
                            domain, attempt, last_error)

        raise LLMError(f"Groq returned invalid structure twice for {domain}: {last_error}")
