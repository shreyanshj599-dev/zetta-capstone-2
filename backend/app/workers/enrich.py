"""Celery task — entry point from the API, exit point to the orchestrator.

Status transitions are driven by Celery signals (Bucket 1: Observer pattern):
the API only sees `queued`; signals push `running` / `succeeded` / `failed`
into the DB without the task body needing to know.
"""

import logging
import uuid

from celery.signals import task_failure, task_prerun

from app.core.celery_app import celery_app
from app.core.db import SessionLocal
from app.repos import company_repo
from app.repos import job_repo
from app.schemas.company import CompanyOut
from app.services import company_cache
from app.services.enrichment import enrich_domain
from app.services.llm.base import LLMError
from app.services.llm.factory import make_provider

log = logging.getLogger(__name__)


@celery_app.task(name="app.workers.enrich.run_enrichment", bind=True)
def run_enrichment(self, job_id: str) -> dict:  # noqa: ANN001 — Celery binds self
    """Run the full enrichment pipeline for one job."""
    job_uuid = uuid.UUID(job_id)
    db = SessionLocal()
    try:
        job = job_repo.get(db, job_uuid)
        if job is None:
            log.warning("run_enrichment_missing_job id=%s", job_id)
            return {"job_id": job_id, "status": "missing"}

        domain = job.domain

        try:
            llm = make_provider()
            company_id = enrich_domain(db, domain, llm)
            job_repo.mark_succeeded(db, job_uuid, uuid.UUID(company_id))
            db.commit()
            company = company_repo.get_by_id(db, uuid.UUID(company_id))
            if company is not None:
                company_cache.set_company(CompanyOut.model_validate(company))
            return {"job_id": job_id, "status": "succeeded", "company_id": company_id}
        except (LLMError, RuntimeError) as e:
            db.rollback()
            job_repo.mark_failed(db, job_uuid, str(e))
            db.commit()
            log.error("run_enrichment_failed job_id=%s err=%s", job_id, e)
            return {"job_id": job_id, "status": "failed", "error": str(e)[:500]}
    finally:
        db.close()


# --- Observer: Celery signals push state transitions into the DB ----------


@task_prerun.connect(sender=run_enrichment)
def _on_prerun(task_id=None, args=None, **kwargs) -> None:  # noqa: ANN001
    if not args:
        return
    job_id = args[0]
    db = SessionLocal()
    try:
        job_repo.mark_running(db, uuid.UUID(job_id))
        db.commit()
    finally:
        db.close()


@task_failure.connect(sender=run_enrichment)
def _on_failure(task_id=None, exception=None, args=None, **kwargs) -> None:  # noqa: ANN001
    """Catch unexpected exceptions that escape the task body."""
    if not args:
        return
    job_id = args[0]
    db = SessionLocal()
    try:
        job_repo.mark_failed(db, uuid.UUID(job_id), str(exception)[:500] if exception else "unknown")
        db.commit()
    finally:
        db.close()
