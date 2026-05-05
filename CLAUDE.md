# Zetta Capstone — Lead Enrichment Service

## What this project is

Submit a company URL → Celery worker scrapes the homepage and a few well-known pages → Groq (Llama 3.3 70B) extracts structured `CompanyFacts` → cached in Postgres by canonical domain → rendered in a Next.js dashboard. Built as the Zetta May-15 cohort capstone; the constraints come from that prep doc.

---

## Hard constraints (do not violate)

1. **Never call the LLM in the request path.** The HTTP handler creates a job row, enqueues a Celery task, and returns. Scrape + LLM happen in the worker. If you find yourself calling `make_provider().extract_company_facts(...)` from anywhere in `app/api/`, stop and route through `workers/enrich.py`.
2. **Cache by canonical domain.** `https://www.foo.com/about`, `Foo.com`, and `foo.com` all collapse to one `companies` row via `app/utils/domain.py:canonicalize_domain`. Don't bypass it.
3. **Respect `robots.txt` and rate-limit per host.** Default 1 req/sec per host; never strip the `User-Agent`.
4. **Structured output is a hard contract.** `CompanyFacts` (`app/schemas/company.py`) is the boundary. Two validation failures = job marked `failed`. We do not store half-parsed JSON.

---

## Conventions

- **Repository pattern for all DB access.** Handlers and tasks call `repos/*_repo.py`. They never `db.execute(...)` directly.
- **Protocol-based DI for LLM providers.** Code depends on `services/llm/base.py:LLMProvider`, never on `GroqProvider`. Add a new provider by dropping a file under `services/llm/` and extending `factory.py` — nothing else changes.
- **Pydantic at the boundaries.** API request/response models live in `schemas/`. SQLAlchemy ORM types stay inside `models/` and `repos/`.
- **Sync SQLAlchemy.** We deliberately avoid async because Celery's async story is messy. FastAPI handlers are `def` (run in threadpool); the worker uses the same `SessionLocal`.
- **No `Any` in Python, no `any` in TS.** mypy strict + Ruff enforced via pre-commit hook.

---

## Gotchas (things that will bite you)

- **Celery on Windows:** `prefork` pool is broken (no `fork()`). `app/core/celery_app.py` already sets `worker_pool='solo'` on Windows, so dev works. Linux containers use prefork normally.
- **psycopg vs psycopg2:** we use `psycopg` v3 (`postgresql+psycopg://`). If you see `ModuleNotFoundError: psycopg2`, your URL is wrong.
- **Groq rate limits:** free tier is ~30 RPM. `verify.sh` is fine; running the eval set in a tight loop will 429. The `@retry` on `services/scraper.py` handles transient HTTP, not Groq quota — that surfaces as `LLMError` and fails the job, which is correct.
- **Next.js dev `/api/*`:** in dev, the frontend hits the backend on `localhost:8000` directly via `NEXT_PUBLIC_API_URL`. In production we don't proxy through Next.js — Vercel routes static, Railway hosts the API.
- **Status transitions are driven by signals, not the task body.** `task_prerun` flips `queued → running`; the task body returns success or `task_failure` flips to `failed`. If you need to add a state, do it via signals so the task body stays focused on work.

---

## Common commands

```bash
# Boot everything
docker compose up -d

# Tail logs (worker is the chatty one)
docker compose logs -f worker

# Apply migrations (also runs automatically on backend boot)
docker compose exec backend alembic upgrade head

# Add a new migration
docker compose exec backend alembic revision --autogenerate -m "describe change"

# Smoke test the golden path
./verify.sh

# Open a psql shell
docker compose exec postgres psql -U zetta -d zetta
```

---

## Decisions log

- **Groq vs Anthropic for the LLM:** picked Groq because (a) free tier is generous enough for the eval set, (b) Llama 3.3 70B's structured-JSON quality on this task is sufficient, (c) it forced the Adapter pattern (we use the OpenAI-compat SDK, not Anthropic's native one). Trade-off: we don't get to exercise the `claude-api` Claude Code skill. Acceptable.
- **selectolax vs BeautifulSoup:** picked selectolax — 10-20× faster on the homepages we hit, and the API is fine for the limited DOM surgery we do (strip script/style/nav). BS4 would be friendlier for deep extraction, but we only need to grab body text.
- **Sync SQLAlchemy vs async:** sync. Celery's async support requires running an asyncio loop inside the worker, which adds complexity for no clear win on a workload that's mostly waiting on HTTP and a single LLM call. Re-evaluate if we ever batch-enrich.
- **Repository pattern:** kept it because the prep doc explicitly grades pattern recognition; this is the cleanest place to point and say "here's DIP in action."

---

## Where to look first

| You want to... | File |
|---|---|
| Add a new endpoint | `app/api/` + `app/schemas/` |
| Change what the LLM extracts | `app/schemas/company.py` (CompanyFacts) + `app/services/llm/groq.py` (system prompt) |
| Swap LLM providers | new file in `app/services/llm/` + edit `factory.py` |
| Tune the scraper | `app/services/scraper.py` (CANDIDATE_PATHS, MAX_TEXT_PER_PAGE) |
| Trace a job that's stuck | `docker compose logs -f worker`; check `enrichment_jobs.status` and `.error` in psql |
| Add a DB column | new migration via `alembic revision --autogenerate`, then update `models/` + `schemas/` + `repos/` |

---

## Test strategy

- **Unit** (`backend/app/tests/unit/`): pure functions (`canonicalize_domain`, prompt builders), mocked LLM. Fast (<1s).
- **Integration** (`backend/app/tests/integration/`): real Postgres via testcontainers, Celery in eager mode, mocked Groq.
- **End-to-end** (`./verify.sh`): boots the whole stack, hits a real cooperative URL, asserts non-empty `industry` and `tech_stack`. This is the script the prep doc wants.
- **Browser** (`tests/e2e/golden-path.spec.ts`, Playwright): paste URL → expect company card within 30s. Future work.
