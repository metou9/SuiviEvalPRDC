# 08 — Implementation Plan

This is the master delivery plan. Each phase is a **vertical slice** that ends in something
**deployable and demonstrable**, so value lands early and risk stays low. Phases map directly to the
manual's monitoring types:

| Phase | Delivers | Manual coverage |
|---|---|---|
| 0 | Infra skeleton | (runtime only) |
| 1 | Foundation + **suivi d'exécution** MVP | physical/operational progress, the data lifecycle, first dashboard |
| 2 | **Suivi financier** + **passation de marchés** + dashboards + quarterly report | finance & procurement |
| 3 | **Suivi d'impact** + **MGP** + reporting + extensibility | impact, grievances, annual report |
| 4 (optional) | Dynamic forms, import, GIS, public portal | nice-to-haves / future |

> Phase boundaries match the per-track summaries in `04_backend_spec.md` §4.9 and
> `05_frontend_spec.md` §5.9; this file is the authoritative, checklist-level expansion.

---

## Definition of Done (applies to **every** task, all phases)

A task is not "done" until:

- [ ] **Project-scoped.** Every query/endpoint/screen operates within the selected project; no
      implicit cross-project access (`X-Project-Id` enforced server-side from membership).
- [ ] **No hard-coded PRDC values in code.** Anything project-specific (geo names, components, targets,
      categories, methods) is reference/seed data, never a literal in source.
- [ ] **Workflow-aware.** New record types use the shared state machine (DRAFT→SUBMITTED→VALIDATED→
      AUDITED→CONSOLIDATED, +REJECTED) and write `StateEvent`; only `CONSOLIDATED` data feeds official
      dashboards/reports.
- [ ] **Permissions enforced.** Capability **and** record-in-scope checks per `03_rbac_and_workflow.md`.
- [ ] **i18n.** All user-facing strings go through `fr.json`/`en.json` (default `fr`). No hard-coded UI
      text.
- [ ] **Responsive.** Verified at 360 / 768 / 1280 px (field entry must work on a phone).
- [ ] **Tested.** Backend: pytest (model/serializer/permission/workflow/calculation as applicable).
      Frontend: a Vitest/RTL test for non-trivial components/hooks.
- [ ] **OpenAPI accurate.** `drf-spectacular` schema regenerates cleanly; the frontend agent can read
      `/api/v1/docs/`.
- [ ] **Audit fields.** `created_at/updated_at/created_by/updated_by` populated; reference data uses
      `is_active` soft-delete.

---

## Phase 0 — Infrastructure skeleton

**Goal:** the four containers run and the host nginx routes correctly, against an empty app.

Tasks:
- [ ] Repo scaffolding per `01_architecture.md` §1.5 (monorepo `backend/`, `frontend/`, `deploy/`).
- [ ] `backend/Dockerfile` + `entrypoint.sh`; minimal Django project (`config/`) that boots and
      serves `/api/v1/docs/`.
- [ ] `frontend/Dockerfile` + container `nginx.conf`; a Vite React app that renders a placeholder.
- [ ] `deploy/postgres/init.sql` (creates `metabaseappdb`, `metabase_app`, `metabase_ro`).
- [ ] `docker-compose.yml` with `db`, `backend`, `metabase`, `frontend` (all `127.0.0.1`).
- [ ] `deploy/nginx.host.conf` installed on host; TLS cert; routes verified.
- [ ] `.env.example` → `.env`.

**Acceptance:** `docker compose up -d` → four healthy containers; `https://<host>/` shows the SPA
placeholder; `https://<host>/api/v1/docs/` loads; `https://<host>/metabase` shows Metabase setup.

---

## Phase 1 — Foundation + Suivi d'exécution (MVP)

**Goal:** log in, configure (or seed) a project, capture indicator measurements and activities, run
them through the collect→validate→audit→consolidate lifecycle, and see a first **physical-results**
Metabase dashboard inside the app.

### Backend track
- [ ] `core`: `Project`, `Milestone`, `ProjectMembership`; abstract `TimeStampedModel`/`AuthoredModel`;
      `CurrentProjectMiddleware` (resolve `X-Project-Id` → `request.project`); generic `StateEvent`;
      **WorkflowMixin** (transition actions + guards) and **scoping** base querysets.
- [ ] `accounts`: custom `User`; `Role`, `RoleAssignment` (geo/program scope); seed the 17 roles;
      capability registry + permission classes; SimpleJWT auth (`/auth/token`, `/refresh`, `/me`).
- [ ] `geo`: `GeoLevel`, `GeoUnit` (self-parenting, rank constraint); CRUD ViewSets + tree endpoint.
- [ ] `program`: `ProgramNode` (self-parenting); CRUD + tree endpoint.
- [ ] `indicators`: `IndicatorType`, `Dimension`, `DimensionCategory`, `Indicator`,
      `IndicatorResponsibility`, `IndicatorDimension`, `IndicatorTarget`, `Measurement`,
      `MeasurementValue`; CRUD + `/measurements/` (filters, bulk create, **transition** actions,
      history); disaggregation reconcile validation (warn).
- [ ] `activities`: single `Activity` (kind enum) + `ActivityParticipant` + generic `Attachment`;
      `/activities/` with per-kind conveniences; workflow.
- [ ] `reporting` (partial): `v_indicator_progress` + `v_activity_rollup` views (migration + grant);
      `/dashboards/indicator-progress/` read endpoint; **Metabase embed endpoint** (`/metabase/embed/`).
- [ ] **Seed commands:** `seed_reference` (generic skeleton) and `seed_prdc` (idempotent reference
      project — the only place PRDC values live; full dataset in `02_domain_and_data_model.md` §2.5).
- [ ] OpenAPI live at `/api/v1/schema/` + `/docs/`.

### Frontend track
- [ ] App shell: `AppShell`, `Topbar`, off-canvas `Sidebar`, `ProjectSwitcher`, `LanguageSwitcher`.
- [ ] Auth: `AuthProvider` (token in memory, refresh in `localStorage`), login screen, `RequireAuth` /
      `RequireCapability` guards, single axios instance (Bearer + `X-Project-Id` interceptors, single
      refresh-retry on 401).
- [ ] i18n bootstrap (`fr` default, `en` fallback); TanStack Query setup; CSS import order per
      `01_architecture.md` §1.4.
- [ ] Reusable components: `ListPage`, `EntityFormDialog`, `WorkflowBadge`, `WorkflowActions`,
      `StateTimeline`, `TreeSelectField`, `PeriodPicker`, `DisaggregationInputs`, `RagIndicator`,
      `KpiCard`, `MetabaseEmbed`.
- [ ] Admin config screens: geo hierarchy, program tree, indicators (+targets, +responsibilities view),
      reference lists, users/roles.
- [ ] **Measurements**: list + **grid entry** (period × geo) + workflow actions + disaggregation.
- [ ] **Activities**: typed forms per Fiche (training, field visit, visit received, meeting, sub-project,
      stakeholder, observation) + participant list + attachments.
- [ ] **Dashboard** page: physical-results Metabase embed + PDO `KpiCard`s + RAG.

### Phase-1 acceptance
- [ ] A user logs in; an admin seeds or configures a project with geography/components/indicators.
- [ ] A field role captures a measurement and an activity; they move DRAFT→…→CONSOLIDATED with the
      correct roles allowed at each step; every transition is in the timeline.
- [ ] Only consolidated measurements appear in `v_indicator_progress`; the physical-results dashboard
      renders **inside the app**, scoped to the project, showing cumul vs current period and RAG.
- [ ] Everything works on a phone; UI defaults to French.

---

## Phase 2 — Suivi financier + Passation de marchés + Dashboards + Quarterly report

**Goal:** budgets, disbursements and realisation tracked by category and component with the manual's
rates; the procurement plan and contract stages tracked with durations; financial & procurement
dashboards; and a generated **quarterly report**.

### Backend track
- [ ] `finance`: `ExpenseCategory`, `FundingSource`, `BudgetLine`, `FinancialTransaction`
      (ENGAGEMENT/DISBURSEMENT/REALIZATION; REALIZATION requires supporting doc to consolidate);
      CRUD + workflow.
- [ ] `procurement`: `ProcurementMethod` (self-parenting), `ProcurementStage`, `PPMItem`,
      `ProcurementProcess`, `StageEvent`; CRUD; **stage board** `advance` action; durations exposed.
- [ ] `reporting` views: `v_financial_by_category`, `v_financial_by_component`, `v_procurement_status`,
      `v_procurement_durations` (migrations + grants); matching `/dashboards/*` endpoints.
- [ ] `reporting/calculations.py`: taux de décaissement, taux de réalisation financière,
      reliquat/dépassement, écarts, procurement realisation rate (canonical logic lives in the views;
      this module backs the `/dashboards/*` endpoints and tests).
- [ ] **Quarterly report** generation (WeasyPrint, in-request) from `ReportTemplate.structure`; generic
      `?format=xlsx` export of the dashboards.
- [ ] Extend `seed_prdc` with the expense categories, funding sources, procurement methods/stages,
      PPM skeleton.

### Frontend track
- [ ] Finance: budget lines screen, transactions screen (typed by kind, supporting-doc upload),
      finance-by-category & finance-by-component dashboards (Metabase embeds + `KpiCard`s for rates).
- [ ] Procurement: PPM list, processes list, **stage board** (Kanban-style advance with
      decisions/deadlines), procurement dashboard (status + durations, overdue highlight).
- [ ] Reports: quarterly report builder/preview + download; `xlsx` export buttons on dashboards.

### Phase-2 acceptance
- [ ] Budgets and transactions entered and consolidated; `v_financial_by_*` reproduces taux de
      décaissement / réalisation financière / reliquat for a hand-checked category, year and component.
- [ ] A procurement process advances through stages; durations and overdue stages show on the board and
      `v_procurement_*`.
- [ ] Finance and procurement dashboards render in-app, scoped, with year filters.
- [ ] A quarterly report PDF generates in-request with physical + financial + procurement sections; an
      xlsx export of the dashboards downloads.

---

## Phase 3 — Suivi d'impact + MGP + Reporting + Extensibility

**Goal:** impact indicators with baseline/latest change tables; the grievance mechanism with SLA
tracking; the annual report; the public/consultation read-only mode; and the responsibilities matrix.

### Backend track
- [ ] `grievances`: `GrievanceType`, `Grievance` (own `state` + data-quality `status`); CRUD +
      `resolve`/`close`/`reject`; `v_grievance_sla` view + dashboard endpoint.
- [ ] Impact: `v_impact_change` view + `/dashboards/impact-change/`; impact-entry conveniences
      (baseline/mid/closing measurements already modelled).
- [ ] **Annual report** template + generation; public/consultation **embeds** (status-locked
      `CONSOLIDATED`, project-locked, no entry routes — realises the manual's separate Saisie/
      Consultation).
- [ ] Responsibilities API surfacing the annex matrix from `IndicatorResponsibility`.
- [ ] Finalise `seed_prdc` (grievance types, impact indicators, milestones/targets complete).

### Frontend track
- [ ] Grievances: intake + management screens, SLA dashboard (% traitées dans le délai).
- [ ] Impact: baseline-vs-latest change tables + impact dashboard.
- [ ] Annual report builder/preview/download.
- [ ] Responsibilities matrix screen (read from `IndicatorResponsibility`) with xlsx/pdf export.
- [ ] Public/consultation read-only mode (VIEWER or public): dashboards + read-only registers, no
      entry actions.

### Phase-3 acceptance
- [ ] Grievances tracked end-to-end; SLA % computed per type/level on the dashboard.
- [ ] Impact change (baseline → latest, abs & %) shown per impact indicator with target context.
- [ ] Annual report generates; public/consultation mode exposes only consolidated data and hides all
      entry routes.
- [ ] The responsibilities matrix reproduces the manual's roles annex and exports.

---

## Phase 4 — Optional enhancements (future)

Scope only if/when needed; none are required for a faithful implementation of the manual.

- [ ] **Dynamic custom forms:** admin-defined fields/forms so a new project can capture bespoke Fiches
      without code changes.
- [ ] **Import:** CSV / **KoboToolbox** import endpoint + wizard (the manual references Kobo for field
      collection) feeding `Measurement`/`Activity` as `source=IMPORT`.
- [ ] **`IndicatorComputation`:** declarative mapping ("indicator X = COUNT of Training where …") to
      auto-derive measurements from activities, replacing manual entry for count-type indicators.
- [ ] **GIS map:** Leaflet/MapLibre map using `GeoUnit.geojson`/lat-long for spatial dashboards.
- [ ] **Public portal:** a dedicated unauthenticated consultation site (beyond in-app public mode).
- [ ] **Offline-light field capture:** queue-and-sync for low-connectivity areas.

---

## Sequencing guidance for the coding agent

1. Build **Phase 0** end-to-end first; a green infra skeleton de-risks everything after.
2. Within a phase, build **one vertical slice at a time** (backend app ↔ matching frontend feature),
   because the folders mirror each other (`01_architecture.md` §1.5). Wire the workflow + scoping into
   the **first** slice (`indicators`) and reuse the mixins for every subsequent record type.
3. Stand up **reporting views + Metabase** as soon as the first consolidated data exists (end of Phase
   1), so the embed mechanics are proven early rather than discovered late.
4. Keep `seed_prdc` growing alongside each app; it doubles as your most realistic test fixture and the
   reference-data acceptance check.
5. Re-read the **Definition of Done** before closing any task.
