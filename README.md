# funk-poc

A minimal FastAPI + Jinja2 + SQLite proof of concept for a policy list (CRUD slice), with search, sorting, pagination headers, CSV export, optional API key, tests, and CI. It demonstrates pragmatic end-to-end delivery: data model → API → UI → tests/CI.

![CI](https://github.com//actions/workflows/ci.yml/badge.svg)

## Table of Contents
- Why
- Stack & Structure
- Features
- Getting Started
- Dev Commands
- Auth (API Key)
- Endpoints
- Search, Sorting & Pagination
- Export (CSV)
- Seed Data
- Tests & CI
- Common Pitfalls
- Next Steps

---

## Why
- Show end-to-end capability with minimal ceremony.
- Demonstrate code discipline: validation, proper HTTP errors (401/409/422), tests, CI.
- Keep the barrier low (SQLite, server-rendered HTML, a sprinkle of JS).

## Stack & Structure
- FastAPI (routing + OpenAPI)
- Pydantic (validation/serialization)
- Jinja2 (server-rendered HTML + small JS)
- SQLite + SQLAlchemy (lightweight DB)
- Uvicorn (ASGI server)
- Pytest + GitHub Actions (CI)
- ES Modules on the client side (small, readable structure)

Project layout:

    funk-poc/
      ├─ main.py
      ├─ templates/
      │   └─ index.html
      ├─ static/
      │   ├─ styles.css
      │   ├─ main.js        # type="module"
      │   ├─ api.js         # fetch wrapper (+ API key header)
      │   └─ ui.js          # UI helpers
      ├─ seeds.json         # sample dataset
      ├─ seed.py            # simple upsert/seed
      ├─ test_app.py        # pytest suite
      ├─ requirements.txt
      ├─ requirements-dev.txt
      ├─ Makefile
      ├─ .github/workflows/ci.yml
      └─ README.md

## Features
- List / search / sort policies
- Create (POST), read (GET), delete (DELETE)
- Pagination headers (X-Total-Count, Content-Range)
- CSV export (honors search & sorting)
- Optional API key via header X-API-Key
- UI: status chips, delete button, “Export CSV”, API-key controls, health pill

## Getting Started

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn main:app --reload
    # UI:  http://127.0.0.1:8000
    # API: http://127.0.0.1:8000/docs

## Dev Commands (Makefile)

    make run    # start uvicorn
    make seed   # load demo data
    make test   # run pytest
    make fmt    # black .

## Auth (API Key)
Set API_KEY to require X-API-Key on all /policies* endpoints. Without API_KEY, auth is off (dev mode).

    API_KEY="change-me" uvicorn main:app --reload
    curl -H "X-API-Key: change-me" "http://127.0.0.1:8000/policies?limit=1"

In the UI you can store the key:

    localStorage.setItem('API_KEY', 'change-me');

## Endpoints
- GET  /health → {status:"ok"}
- GET  /version → {app, version}
- GET  / → server-rendered list (Jinja2)
- GET  /policies → JSON list (supports q, sort, dir, limit, offset)
- GET  /policies/{id} → JSON item (404 if not found)
- POST /policies → create (201), 409 on duplicate number, 422 on validation
- DELETE /policies/{id} → 204, 404 if not found
- GET  /policies.csv → CSV export (honors q, sort, dir)

List headers:

    X-Total-Count: <total>
    Content-Range: policies <from>-<to>/<total>

## Search, Sorting & Pagination
- q — fuzzy on number, holder, status
- sort — one of: id | number | holder | premium | status
- dir — asc | desc
- limit (1–100), offset (≥0)

Example:

    curl "http://127.0.0.1:8000/policies?q=act&sort=premium&dir=asc&limit=10&offset=0"

## Export (CSV)

    curl "http://127.0.0.1:8000/policies.csv?q=act&sort=number&dir=asc" -o policies.csv

## Seed Data

    python seed.py
    # idempotent (INSERT OR IGNORE), ensures unique index on number

## Tests & CI
- pytest -q → green suite (env-independent, isolated test DB).
- GitHub Actions (.github/workflows/ci.yml) runs tests on push/PR.

## Common Pitfalls
- 401 Unauthorized: API key missing/wrong → set API_KEY and send X-API-Key.
- 409 Conflict: duplicate number → enforced by unique index and API.
- 422 Unprocessable Entity: validation failed (e.g., holder min length).
- 405 Method Not Allowed: wrong HTTP verb (e.g., HEAD vs GET).

## Next Steps
- Inline edit (PUT/PATCH).
- Simple roles/permissions if needed (read vs write).
- Move from SQLite to Postgres (prod).
- Alembic migrations.
