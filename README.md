# Zetta Capstone - Lead Enrichment Service

Submit a company URL, run the enrichment work in the background, extract structured company facts with Groq Llama 3.3 70B, save the result in Postgres, and view it in a Next.js dashboard.

## Why

Built as the Zetta May-15 cohort capstone. The constraints are FastAPI, Celery, Postgres, Next.js, LLM structured output, one-command dev, and a golden-path test.

## Stack

- **Backend:** FastAPI, SQLAlchemy 2.0, psycopg3, Alembic
- **Worker:** Celery with Redis broker/result backend
- **LLM:** Groq Llama 3.3 70B with Pydantic v2 structured output
- **Frontend:** Next.js 15 App Router
- **Dev:** Docker Compose

## Quickstart

```bash
cp .env.example .env
# Fill GROQ_API_KEY in .env
docker compose up -d
./verify.sh
```

Open:

- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`

The local stack starts:

- `frontend`
- `backend`
- `worker` using Celery `threads` pool with concurrency `4`
- `postgres`
- `redis`

## Render

This repo includes a `render.yaml` Blueprint for:

- `zetta-frontend`: public Next.js web app
- `zetta-backend`: FastAPI web service
- `zetta-worker`: Celery background worker using `--pool=threads --concurrency=4`
- `zetta-postgres`: Postgres database
- `zetta-redis`: Render Key Value instance used as Celery broker/result backend

Deploy:

```bash
git add .
git commit -m "Add frontend and threaded Celery Render deploy"
git push origin main
```

Then create or sync a Render Blueprint from `render.yaml`. Render will ask for `GROQ_API_KEY`; paste your Groq key there.

Open the public URL shown for `zetta-frontend`.

## API

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/enrich` | Submit a company URL and receive a job |
| `GET` | `/api/enrich/{job_id}` | Read job state and company payload when ready |
| `GET` | `/api/companies` | List cached companies; supports `?industry=&limit=` |
| `GET` | `/api/companies/{domain}` | Get one company by canonical domain |
| `GET` | `/health` | Health check |
