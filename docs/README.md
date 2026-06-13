# M&E Platform — Implementation Specification

**Codename:** `me-platform` · **Reference deployment:** PRDC‑VFS (Mauritania, World Bank P179449)

This repository contains the complete, build‑ready specification for a **generic Monitoring &
Evaluation (Suivi‑Évaluation) platform**. It is derived from the *Manuel de Suivi‑Évaluation du
PRDC‑VFS*, but **nothing about PRDC is hard‑coded**: the project, its geography, its programme
structure, its indicators, its expense categories and its procurement methods are all **reference
data** that an administrator configures. PRDC‑VFS is shipped only as the **first seeded project**
(see `02_domain_and_data_model.md`, “Seed data”).

The system implements the manual end‑to‑end:

- **Suivi d’exécution** (physical/operational progress against planning).
- **Suivi financier** (budget, disbursements, financial realisation, by category and component).
- **Suivi de la passation de marchés** (procurement plan, contracts, stage durations).
- **Suivi d’impact** (impact indicators, baseline/mid‑term/closing measurements, change tables).
- **MGP** (Mécanisme de Gestion des Plaintes / grievance redress).
- The **data lifecycle** from the manual’s roles annex: *collect → validate → audit → consolidate
  (transfer to MIS) → aggregate → analyse*, with full traceability.
- **Tableaux de bord** delivered through **Metabase**, embedded in the application.

---

## 1. Technology stack (decided — do not substitute without reason)

| Layer | Technology | Pinned target |
|---|---|---|
| Database | PostgreSQL | 16 |
| Backend | Python + Django + Django REST Framework | Python 3.12, Django 5.2 LTS, DRF 3.16.x |
| Dashboards/BI | Metabase (OSS), signed (static) embedding via JWT | latest stable OSS tag |
| Frontend | ReactJS + Vite + PrimeReact + Bootstrap | React 18.3.x, Vite 6, PrimeReact 10.9.x, Bootstrap 5.3.x |
| Reverse proxy | **nginx installed on the host** (TLS, single entry point) | distro nginx |
| Packaging | Docker + Docker Compose | Compose v2 |
| Calls | **Synchronous request/response only** — no Celery, no broker, no websockets | — |

Rationale and exact dependency lists are in `01_architecture.md`.

> **Why Django 5.2 LTS** (not 6.0): an institutional, World‑Bank‑funded system benefits from the
> ~3‑year LTS support window. 6.0 is the latest but short‑term.
> **Why React 18.3 + PrimeReact 10.9:** this is the friction‑free pairing. PrimeReact 10.9 also
> declares React 19 in its peer range, so React 19 is acceptable if the team prefers it; 11.x is
> still pre‑release and must not be used.
> **Why synchronous:** the data volume (tens of communes, hundreds of indicators/records per
> period) is small. Synchronous DRF views + gunicorn sync workers keep the system simple,
> debuggable and easy to operate. Exports (Excel/PDF) are generated in‑request.

---

## 2. How a coding agent should use this spec

Read the documents **in order**. They are written to be executed top‑to‑bottom.

| # | File | Purpose |
|---|---|---|
| 0 | `README.md` | This file. Orientation + global build order. |
| 1 | `01_architecture.md` | Stack, versions, repo layout, runtime topology, cross‑cutting conventions. |
| 2 | `02_domain_and_data_model.md` | The generic domain, the parametrization strategy, the full data model (ERD + every table), and the PRDC seed dataset. |
| 3 | `03_rbac_and_workflow.md` | Roles, the permission matrix, the record state machine, scoping rules, audit trail. |
| 4 | `04_backend_spec.md` | Django apps, models, settings, the complete REST endpoint catalogue, business logic (the rate calculations), exports, the Metabase token endpoint, tests. |
| 5 | `05_frontend_spec.md` | React structure, routing, layout, responsiveness, the full screen catalogue, reusable components, the API/service layer, i18n, dashboard embedding. |
| 6 | `06_dashboards_metabase.md` | The reporting SQL views (the heart of the dashboards), Metabase provisioning, the dashboard catalogue mapped to the manual, embedding mechanics. |
| 7 | `07_deployment.md` | Dockerfiles, `docker-compose.yml`, the **host** nginx config, environment variables, DB init SQL, operational runbook. |
| 8 | `08_implementation_plan.md` | The phased plan (Phase 1–3 + optional Phase 4) with per‑track task checklists and acceptance criteria. |

### Global build order

1. **Infra skeleton** — `07_deployment.md`: bring up `db` + an empty `backend` + `metabase` with `docker compose up`. Confirm the host nginx routes `/api`, `/`, `/metabase`.
2. **Backend foundation** — `04_backend_spec.md` Phase‑1 apps: `core`, `accounts`, `geo`, `program`, `indicators`. Migrations + seed command + auth.
3. **Frontend foundation** — `05_frontend_spec.md` Phase‑1: shell, auth, layout, reference‑data admin screens, indicator measurement entry.
4. **Workflow** — `03_rbac_and_workflow.md`: state machine + permissions wired into both ends.
5. **Reporting views + Metabase** — `06_dashboards_metabase.md`: create the SQL views, provision Metabase, embed the physical‑results dashboard.
6. Continue per `08_implementation_plan.md` (financial, procurement, impact, MGP, reporting, extensibility).

### Conventions the agent must keep

- **Two‑digit ordered file prefixes** in this spec map to logical milestones; keep that discipline in code (clear app boundaries).
- **French is the default UI locale** (`fr`); all user‑facing strings go through i18n with an `en` fallback. Domain data is stored as entered (French).
- **Everything is project‑scoped.** Every query, endpoint and screen operates within a selected `Project`. Never write a query that crosses projects implicitly.
- **No hard‑coded PRDC values in code.** If you find yourself typing "Wilaya", "Trarza", "Travaux", or a target number into source, it belongs in seed data instead.
- **Sync only.** If a task seems to "want" a background worker, do it in‑request and stream if large. Do not add Celery/Redis.

---

## 3. What “done” means

Each phase in `08_implementation_plan.md` has explicit acceptance criteria. At the end of Phase 1
a user can log in, an admin can configure (or seed) a project with its geography/components/
indicators, field roles can capture measurements and activities, those records move through the
collect→validate→audit→consolidate lifecycle, and a first Metabase dashboard of physical results is
visible inside the app. Phases 2–3 add finance, procurement, impact, grievances, reporting and
extensibility.
