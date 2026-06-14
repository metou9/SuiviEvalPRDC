# M&E Platform (`me-platform`)

Generic **Monitoring & Evaluation (Suivi-Évaluation)** platform, reference deployment
**PRDC-VFS** (Mauritania, World Bank P179449). Nothing about PRDC is hard-coded — the
project, geography, programme tree, indicators, expense categories and procurement
methods are all **reference data** seeded via `seed_prdc`.

Full specification lives in [`docs/`](docs/) (read in order, `01`→`08`).

## Implementation status

- **Phase 0 — Infra skeleton:** `docker-compose.yml`, backend & frontend Dockerfiles,
  host nginx config, Postgres `init.sql`, `.env.example`, entrypoint. ✅
- **Phase 1 — Foundation + Suivi d'exécution:** `core`/`accounts`/`geo`/`program`/
  `indicators`/`activities` apps, JWT auth, RBAC (capabilities + geo scope), the shared
  workflow state machine, `seed_prdc`/`seed_reference`, `v_indicator_progress` +
  `v_activity_rollup` views, Metabase signed-embed endpoint; SPA shell, auth, i18n,
  measurements (list + grid entry + workflow), activities, indicators, admin config,
  the physical-results dashboard. ✅
- **Phase 2 — Finance + Procurement + Dashboards + Quarterly report:** `finance` &
  `procurement` apps, financial/procurement views + `/dashboards/*` endpoints,
  `reporting/calculations.py`, quarterly report (WeasyPrint); SPA finance (budget,
  transactions, dashboard) and procurement (PPM, stage board, dashboard) + reports. ✅
- Phase 3 (grievances workflow, impact, annual report, public mode) — not in scope here
  (grievance-type reference data + models are present).

## Layout

```
backend/   Django 5.2 + DRF (apps/, config/), pytest suite
frontend/  React 18 + Vite + PrimeReact SPA
deploy/    host nginx, postgres init.sql
docs/      the build-ready specification
docker-compose.yml, .env.example
```

## Quick start (Docker)

```bash
cp .env.example .env          # fill secrets
docker compose up -d db       # init.sql creates metabaseappdb + metabase_ro
docker compose up -d backend  # migrate + collectstatic (creates v_* views)
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py seed_prdc   # idempotent reference project
docker compose up -d metabase frontend
```

Then provision Metabase per `docs/06_dashboards_metabase.md` §6.3, put the dashboard IDs
and embedding secret in `.env`, and `docker compose build frontend && docker compose up -d`.

## Local development

Backend:

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
# Postgres (for the reporting views) — set DB_NAME/DB_USER/DB_PASSWORD/DB_HOST, or omit
# all of them to use a zero-config SQLite db (views are skipped on SQLite).
python manage.py migrate
python manage.py seed_prdc
python manage.py runserver
pytest                         # workflow, RBAC/scope, calculations, API, seed
```

API docs at `/api/v1/docs/`. Demo users seeded by `seed_prdc` (password `demo12345`):
`prdc_admin`, `prdc_me`, `prdc_validator`, `prdc_auditor`, `prdc_field`, `prdc_raf`,
`prdc_proc`.

Frontend:

```bash
cd frontend
npm install
npm run dev      # Vite proxies /api and /metabase to the compose stack
npm run test     # Vitest
npm run build
```
