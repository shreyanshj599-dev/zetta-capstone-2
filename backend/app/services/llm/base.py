"""LLM provider interface.

Protocol-based DI (Bucket 1: Strategy pattern + SOLID DIP). Callers depend
on `LLMProvider`, never on a concrete implementation. To add a new provider
(Anthropic, OpenAI, etc.) drop a new file under this package — no changes
to callers.
"""

from typing import Protocol

from app.schemas.company import CompanyFacts
from app.services.scraper import FetchedPage


class LLMError(Exception):
    """Raised when the LLM call fails or returns invalid structure twice."""


class LLMProvider(Protocol):
    def extract_company_facts(self, domain: str, pages: list[FetchedPage]) -> CompanyFacts:
        """Given scraped pages, return validated CompanyFacts.

        Implementations MUST:
        - Validate the model output against CompanyFacts (Pydantic).
        - Retry at most once on validation failure, feeding the validation
          error back into the prompt.
        - Raise LLMError if both attempts fail.
        """
        ...
