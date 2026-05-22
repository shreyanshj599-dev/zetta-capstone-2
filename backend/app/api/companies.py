from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.repos import company_repo
from app.schemas.company import CompanyOut
from app.services import company_cache
from app.utils.domain import canonicalize_domain

router = APIRouter(tags=["companies"])


@router.get("/companies", response_model=list[CompanyOut])
def list_companies(
    db: Session = Depends(get_db),
    industry: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[CompanyOut]:
    companies = company_repo.list_all(db, industry=industry, limit=limit)
    payloads = [CompanyOut.model_validate(c) for c in companies]
    for company in payloads:
        company_cache.set_company(company)
    return payloads


@router.get("/companies/{domain}", response_model=CompanyOut)
def get_company(domain: str, db: Session = Depends(get_db)) -> CompanyOut:
    canonical_domain = canonicalize_domain(domain)
    cached_company = company_cache.get_company(canonical_domain)
    if cached_company is not None:
        return cached_company

    company = company_repo.get_by_domain(db, canonical_domain)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    payload = CompanyOut.model_validate(company)
    company_cache.set_company(payload)
    return payload


@router.get("/companies/{domain}/cache")
def get_company_cache_status(domain: str) -> dict:
    canonical_domain = canonicalize_domain(domain)
    return company_cache.cache_status(canonical_domain)
