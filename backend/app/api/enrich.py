import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.repos import company_repo, job_repo
from app.schemas.company import CompanyOut
from app.schemas.job import EnrichRequest, JobOut
from app.utils.domain import canonicalize_domain
from app.workers.enrich import run_enrichment

router = APIRouter(tags=["enrich"])


@router.post("/enrich", status_code=status.HTTP_202_ACCEPTED, response_model=JobOut)
def submit_enrichment(req: EnrichRequest, db: Session = Depends(get_db)) -> JobOut:
    domain = canonicalize_domain(str(req.url))
    job = job_repo.create(db, domain=domain)
    db.commit()
    # Hand off to Celery — the request path never blocks on scrape or LLM.
    run_enrichment.delay(str(job.id))
    return JobOut.model_validate(job)


@router.get("/enrich/{job_id}", response_model=JobOut)
def get_enrichment(job_id: uuid.UUID, db: Session = Depends(get_db)) -> JobOut:
    job = job_repo.get(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    company_payload: CompanyOut | None = None
    if job.company_id is not None:
        company = company_repo.get_by_id(db, job.company_id)
        if company is not None:
            company_payload = CompanyOut.model_validate(company)

    out = JobOut.model_validate(job)
    out.company = company_payload
    return out
