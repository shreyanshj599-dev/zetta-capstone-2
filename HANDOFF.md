# Handoff — picking up tomorrow

Last worked: **2026-05-05**.

## Where we are

41 files committed locally across 2 commits. Backend is **code-complete** — every file in [`backend/app/`](./backend/app/) is the real implementation, not a stub:
- 4 API endpoints ([`backend/app/api/`](./backend/app/api/))
- Sync SQLAlchemy 2.0 models ([`backend/app/models/`](./backend/app/models/)) + Alembic migration ([`backend/alembic/versions/0001_initial.py`](./backend/alembic/versions/0001_initial.py))
- Repository pattern ([`backend/app/repos/`](./backend/app/repos/))
- Real `httpx + selectolax` scraper with `@retry` ([`backend/app/services/scraper.py`](./backend/app/services/scraper.py))
- Real Groq adapter with two-attempt Pydantic validation ([`backend/app/services/llm/groq.py`](./backend/app/services/llm/groq.py))
- Celery worker with signal-driven status transitions ([`backend/app/workers/enrich.py`](./backend/app/workers/enrich.py))
- `docker-compose.yml` (postgres + redis + backend + worker)
- `verify.sh` golden-path smoke test
- `CLAUDE.md` (the prep-doc deliverable)

The system has **never been booted** — code parses (`compileall` clean) but no service has actually started.

## To resume

1. **Start Docker Desktop.** Wait for the whale icon to confirm "running."
2. **Get a Groq API key** at <https://console.groq.com/keys> and paste into `.env`:
   ```powershell
   Copy-Item .env.example .env  # if .env doesn't exist yet
   notepad .env                 # set GROQ_API_KEY=gsk_...
   ```
3. **(Optional) Install gh CLI** if pushing to GitHub:
   ```powershell
   winget install --id GitHub.cli -e
   gh auth login
   ```
4. **Boot + smoke-test:**
   ```bash
   docker compose up -d
   docker compose logs -f backend     # in another terminal — watch alembic upgrade run
   curl http://localhost:8000/health  # should return {"ok":true}
   ./verify.sh                        # POSTs anthropic.com, polls, asserts
   ```

## Likely first-boot issues to expect

- **`alembic upgrade head` fails on `gen_random_uuid()`** — the migration runs `CREATE EXTENSION pgcrypto`; if the postgres user lacks superuser, this fails. The default compose `postgres:16-alpine` runs `POSTGRES_USER` as superuser so this should be fine, but flag if you see it.
- **Worker imports fail** — if the worker container can't import `app.workers.enrich`, check that `backend/app/__init__.py` exists (it does) and that the volume mount in compose works on Windows (sometimes Docker Desktop needs the drive shared in Settings → Resources → File sharing).
- **Groq returns invalid JSON twice** — bumps the job to `failed` with the validation error stored in `enrichment_jobs.error`. Check `docker compose logs worker` for the full prompt + response. Tweak the system prompt in [`backend/app/services/llm/groq.py:18`](./backend/app/services/llm/groq.py).
- **Celery on Windows** — already handled (`worker_pool='solo'` in `core/celery_app.py`); if you see `AttributeError: module 'os' has no attribute 'fork'`, that wiring broke.

## After the smoke test passes

In rough priority order:
1. **Frontend** (deferred from today): Next.js 15 App Router + Shadcn + Tailwind. Server Component for company list, Client Component for the enrich form + polling. Plan mode is in [`C:\Users\VIVOBOOK\.claude\plans\give-me-a-proper-soft-sundae.md`](C:\Users\VIVOBOOK\.claude\plans\give-me-a-proper-soft-sundae.md) Day 13.
2. **Custom subagents** ([`.claude/agents/prompt-tuner.md`](.claude/agents/prompt-tuner.md), [`.claude/agents/schema-reviewer.md`](.claude/agents/schema-reviewer.md)) — see plan Day 12 + 14.
3. **Custom skills** (`/verify`, `/seed-db`, `/prompt-eval`) — see plan Day 15.
4. **Playwright golden-path test** — see plan Day 15.
5. **Deploy to Railway + Vercel** — see plan Day 16.
6. **Push to GitHub** (after gh CLI is installed) — `gh repo create zetta-capstone --public --push --source=.`.

## Decisions already made (don't re-litigate)

See `CLAUDE.md` "Decisions log" section: Groq vs Anthropic (Groq), selectolax vs BeautifulSoup (selectolax), sync vs async SQLAlchemy (sync). All deliberate.
