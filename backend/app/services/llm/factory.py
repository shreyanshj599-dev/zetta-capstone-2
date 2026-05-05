"""Provider factory (Bucket 1: Factory pattern). Env-driven selection.

Today we only have GroqProvider, but the indirection means adding a second
provider is a one-line change here.
"""

import os

from app.services.llm.base import LLMProvider
from app.services.llm.groq import GroqProvider


def make_provider() -> LLMProvider:
    name = os.getenv("LLM_PROVIDER", "groq").lower()
    if name == "groq":
        return GroqProvider()
    raise ValueError(f"Unknown LLM_PROVIDER: {name}")
