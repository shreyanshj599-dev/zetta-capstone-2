import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, HttpUrl

from app.schemas.company import CompanyOut

JobStatus = Literal["queued", "running", "succeeded", "failed"]


class EnrichRequest(BaseModel):
    url: HttpUrl


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    domain: str
    status: JobStatus
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    company: CompanyOut | None = None
