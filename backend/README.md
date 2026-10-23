# Expense Tracker — Backend

FastAPI (Python 3.12) + Supabase. All routes are under `/api`.

## Structure

```
app/
  main.py                      app factory, /api prefix, health check
  core/config.py               env settings (SUPABASE_URL, SUPABASE_KEY, APP_TIMEZONE)
  core/errors.py               every error -> {"error": "message"}; validation -> 400
  core/clock.py                "today" in the configured timezone
  schemas/expense.py           request validation + response models
  repositories/expense_repo.py Supabase queries (behind a Protocol, faked in tests)
  services/expense_service.py  pagination, totals, monthly summary
  api/routes/expenses.py       HTTP layer
sql/001_create_expenses.sql    table, indexes, RLS, aggregate functions
tests/                         pytest, in-memory fake repo (no Supabase needed)
scripts/package.sh             builds the Beanstalk zip
```

## Setup

1. In Supabase → SQL editor, run `sql/001_create_expenses.sql`.
2. Fill in `backend/.env` (copy of `.env.example`) with the project URL and **secret** key.
3. Install and run:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Docs: http://localhost:8000/api/docs

## Tests

```bash
.venv/bin/pytest
```

## API

| Method | Path | Notes |
|---|---|---|
| POST | `/api/expenses` | `{title, amount, category, date?}` → 201 |
| GET | `/api/expenses` | `?category=&from=&to=&page=&limit=` (limit default 10, max 100) → `{items, total_count, total_amount}` |
| DELETE | `/api/expenses/{id}` | 204, 404 if missing |
| GET | `/api/expenses/summary?month=YYYY-MM` | `{month, totals: {food, travel, bills, other}, total}` |
| GET | `/api/health` | Beanstalk health check |

`total_amount` is computed in Postgres over **all** matching rows, not the current page.

## Deploy (Elastic Beanstalk, Python 3.12 platform)

```bash
./scripts/package.sh   # -> dist/backend-<timestamp>.zip
```

Upload the zip in the Beanstalk console (Upload and deploy). Set environment properties
`SUPABASE_URL`, `SUPABASE_KEY` (and optionally `APP_TIMEZONE`) under Configuration → Updates, monitoring
and logging → Environment properties. The `Procfile` runs gunicorn with uvicorn workers on port 8000
(the platform's nginx proxies to it), and `.ebextensions` sets the health check to `/api/health`.
