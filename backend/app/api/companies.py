from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.repos import company_repo
from app.schemas.company import CompanyOut

router = APIRouter(tags=["companies"])


@router.get("/companies", response_model=list[CompanyOut])
def list_companies(
    db: Session = Depends(get_db),
    industry: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[CompanyOut]:
    companies = company_repo.list_all(db, industry=industry, limit=limit)
    return [CompanyOut.model_validate(c) for c in companies]


@router.get("/companies/{domain}", response_model=CompanyOut)
def get_company(domain: str, db: Session = Depends(get_db)) -> CompanyOut:
    company = company_repo.get_by_domain(db, domain.lower())
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyOut.model_validate(company)
