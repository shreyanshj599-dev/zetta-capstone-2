"""Repository pattern for Company. All DB access lives here.

API handlers and worker tasks call these methods; they never touch
SQLAlchemy sessions directly. This is the Dependency Inversion line.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.schemas.company import CompanyFacts


def get_by_domain(db: Session, domain: str) -> Company | None:
    return db.scalar(select(Company).where(Company.domain == domain))


def get_by_id(db: Session, company_id: uuid.UUID) -> Company | None:
    return db.get(Company, company_id)


def list_all(
    db: Session, industry: str | None = None, limit: int = 50
) -> list[Company]:
    stmt = select(Company).order_by(Company.enriched_at.desc()).limit(limit)
    if industry is not None:
        stmt = stmt.where(Company.industry == industry)
    return list(db.scalars(stmt))


def upsert_from_facts(
    db: Session, domain: str, facts: CompanyFacts, source_urls: list[str]
) -> Company:
    """Insert or update a Company row from a validated CompanyFacts payload."""
    existing = get_by_domain(db, domain)
    payload = {
        "name": facts.name,
        "industry": facts.industry,
        "size_bucket": facts.size_bucket,
        "hq_country": facts.hq_country,
        "tech_stack": facts.tech_stack,
        "hiring_signals": facts.hiring_signals.model_dump(),
        "icp_fit_score": facts.icp_fit_score,
        "raw_extract": facts.model_dump(),
        "source_urls": source_urls,
    }
    if existing is None:
        company = Company(domain=domain, **payload)
        db.add(company)
    else:
        company = existing
        for k, v in payload.items():
            setattr(company, k, v)
    db.flush()
    return company
