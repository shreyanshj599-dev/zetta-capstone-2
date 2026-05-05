"""Orchestrator: scrape → LLM → repo. The worker calls only this.

Keeping the worker thin and the orchestrator pure makes both easier to
test (the orchestrator takes a Session — no Celery, no Redis, no globals).
"""

import logging

from sqlalchemy.orm import Session

from app.repos import company_repo
from app.services.llm.base import LLMError, LLMProvider
from app.services.scraper import fetch_pages

log = logging.getLogger(__name__)


def enrich_domain(db: Session, domain: str, llm: LLMProvider) -> str:
    """Scrape, extract, persist. Returns the company_id (str) on success.

    Raises LLMError or RuntimeError on failure; the worker catches and
    marks the job failed.
    """
    log.info("enrich_start domain=%s", domain)
    pages = fetch_pages(domain)
    if not pages:
        raise RuntimeError(f"No pages could be fetched for {domain}")

    facts = llm.extract_company_facts(domain, pages)
    company = company_repo.upsert_from_facts(
        db, domain=domain, facts=facts, source_urls=[p.url for p in pages]
    )
    log.info("enrich_ok domain=%s company_id=%s", domain, company.id)
    return str(company.id)


__all__ = ["enrich_domain", "LLMError"]
