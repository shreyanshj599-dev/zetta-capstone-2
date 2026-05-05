FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install \
      "fastapi>=0.115" "uvicorn[standard]>=0.32" \
      "pydantic>=2.9" "pydantic-settings>=2.6" \
      "sqlalchemy>=2.0.36" "psycopg[binary]>=3.2" "alembic>=1.13" \
      "celery[redis]>=5.4" "redis>=5.2" \
      "httpx>=0.27" "selectolax>=0.3.25" "tenacity>=9.0" \
      "openai>=1.55" "structlog>=24.4"

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
