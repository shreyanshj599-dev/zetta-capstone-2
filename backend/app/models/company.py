import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, SmallInteger, String, func, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    domain: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    industry: Mapped[str | None] = mapped_column(String, nullable=True)
    size_bucket: Mapped[str | None] = mapped_column(String, nullable=True)
    hq_country: Mapped[str | None] = mapped_column(String, nullable=True)
    tech_stack: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default=text("'{}'::text[]")
    )
    hiring_signals: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    icp_fit_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    raw_extract: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source_urls: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default=text("'{}'::text[]")
    )
    enriched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "icp_fit_score IS NULL OR (icp_fit_score BETWEEN 0 AND 100)",
            name="companies_icp_fit_score_range",
        ),
        Index("companies_industry_idx", "industry"),
    )
