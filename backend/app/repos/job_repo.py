"""Repository pattern for EnrichmentJob."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.job import EnrichmentJob


def create(db: Session, domain: str) -> EnrichmentJob:
    job = EnrichmentJob(domain=domain, status="queued")
    db.add(job)
    db.flush()
    return job


def get(db: Session, job_id: uuid.UUID) -> EnrichmentJob | None:
    return db.get(EnrichmentJob, job_id)


def mark_running(db: Session, job_id: uuid.UUID) -> None:
    job = db.get(EnrichmentJob, job_id)
    if job is not None:
        job.status = "running"
        job.started_at = datetime.now(UTC)
        db.flush()


def mark_succeeded(db: Session, job_id: uuid.UUID, company_id: uuid.UUID) -> None:
    job = db.get(EnrichmentJob, job_id)
    if job is not None:
        job.status = "succeeded"
        job.company_id = company_id
        job.finished_at = datetime.now(UTC)
        db.flush()


def mark_failed(db: Session, job_id: uuid.UUID, error: str) -> None:
    job = db.get(EnrichmentJob, job_id)
    if job is not None:
        job.status = "failed"
        job.error = error[:1000]
        job.finished_at = datetime.now(UTC)
        db.flush()
