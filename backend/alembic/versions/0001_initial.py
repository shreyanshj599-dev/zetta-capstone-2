"""initial schema: companies + enrichment_jobs

Revision ID: 0001
Revises:
Create Date: 2026-05-05

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # pgcrypto provides gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "companies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("domain", sa.String, nullable=False, unique=True),
        sa.Column("name", sa.String, nullable=True),
        sa.Column("industry", sa.String, nullable=True),
        sa.Column("size_bucket", sa.String, nullable=True),
        sa.Column("hq_country", sa.String, nullable=True),
        sa.Column(
            "tech_stack",
            postgresql.ARRAY(sa.String),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column(
            "hiring_signals",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("icp_fit_score", sa.SmallInteger, nullable=True),
        sa.Column("raw_extract", postgresql.JSONB, nullable=False),
        sa.Column(
            "source_urls",
            postgresql.ARRAY(sa.String),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column(
            "enriched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "icp_fit_score IS NULL OR (icp_fit_score BETWEEN 0 AND 100)",
            name="companies_icp_fit_score_range",
        ),
    )
    op.create_index("companies_industry_idx", "companies", ["industry"])

    op.create_table(
        "enrichment_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("domain", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False),
        sa.Column("error", sa.String, nullable=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('queued','running','succeeded','failed')",
            name="enrichment_jobs_status_check",
        ),
    )
    op.create_index("enrichment_jobs_status_idx", "enrichment_jobs", ["status"])


def downgrade() -> None:
    op.drop_index("enrichment_jobs_status_idx", table_name="enrichment_jobs")
    op.drop_table("enrichment_jobs")
    op.drop_index("companies_industry_idx", table_name="companies")
    op.drop_table("companies")
