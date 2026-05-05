# Zetta Capstone — Lead Enrichment Service

Submit a company URL → background worker scrapes the site → Groq (Llama 3.3 70B) extracts structured company facts → cached in Postgres → rendered in a Next.js dashboard.

## Why

Built as the Zetta May-15 cohort capstone. The constraints (FastAPI + Celery + Postgres + Next.js + LLM + structured output + one-command dev + golden-path test) come from the prep doc.

## Stack

- **Backend:** FastAPI, SQLAlchemy 2.0 (sync, psycopg3), Celery + Redis, Alembic
- **LLM:** Groq Llama 3.3 70B via OpenAI-compatible SDK, Pydantic v2 structured output
- **Frontend:** Next.js 15 (App Router), Shadcn, Tailwind, Zustand
- **Dev:** Docker Compose (one-command boot), Playwright + `verify.sh` (golden path)

## Quickstart

```bash
cp .env.example .env       # fill in GROQ_API_KEY
docker compose up -d
./verify.sh                # POST anthropic.com → poll → assert
```

Then open http://localhost:3000.

## Design notes

See [CLAUDE.md](./CLAUDE.md) for hard constraints, conventions, gotchas, and the decisions log.

## API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/enrich` | `{url}` → `{job_id, status}` |
| `GET`  | `/api/enrich/{job_id}` | job state + company payload when ready |
| `GET`  | `/api/companies` | list cached companies; `?industry=&limit=` |
| `GET`  | `/api/companies/{domain}` | single company by canonical domain |
