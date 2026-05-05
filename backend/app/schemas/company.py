import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Industry = Literal[
    "saas", "fintech", "healthcare", "ecommerce", "hardware", "consulting", "other"
]
SizeBucket = Literal["1-10", "11-50", "51-200", "201-1000", "1000+"]


class HiringSignals(BaseModel):
    """Hiring posture extracted from careers/jobs pages."""

    is_hiring: bool
    open_role_count: int = Field(ge=0)
    target_roles: list[str] = Field(default_factory=list, max_length=10)


class CompanyFacts(BaseModel):
    """Hard contract for the LLM output. Validation failure = job failure."""

    model_config = ConfigDict(extra="forbid")

    name: str
    industry: Industry
    size_bucket: SizeBucket
    hq_country: str | None = None
    tech_stack: list[str] = Field(default_factory=list, max_length=20)
    hiring_signals: HiringSignals
    icp_fit_score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)


class CompanyOut(BaseModel):
    """API response shape for /api/companies."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    domain: str
    name: str | None
    industry: str | None
    size_bucket: str | None
    hq_country: str | None
    tech_stack: list[str]
    hiring_signals: dict
    icp_fit_score: int | None
    source_urls: list[str]
    enriched_at: datetime
