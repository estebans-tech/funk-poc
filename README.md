# funk-poc

![CI](https://github.com/estebans-tech/funk-poc/actions/workflows/ci.yml/badge.svg)


Mini-POC med FastAPI + Jinja2 + SQLite.

## Snabbstart
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
Öppna http://127.0.0.1:8000

## Ops-friendly
- `GET /health` – snabb readiness check
- `GET /version` – versionsinfo

## Make targets
- `make run` – starta devserver
- `make seed` – fyll demo-data
- `make test` – kör pytest
- `make fmt` – autoformat (black)

## Export & Sortering
- `GET /policies.csv` – export av nuvarande dataset (stöd för `q`, `sort`, `dir`).
- `GET /policies` – stödjer `?q=<text>&sort=<id|number|holder|premium|status>&dir=<asc|desc>`.

Exempel:
```bash
curl "http://127.0.0.1:8000/policies.csv?q=act&sort=number&dir=asc" -o policies.csv
