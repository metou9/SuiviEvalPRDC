# 05 — Frontend specification (React + Vite + PrimeReact + Bootstrap)

A responsive SPA. PrimeReact for all interactive widgets, Bootstrap grid + PrimeFlex for layout,
axios + TanStack Query for synchronous request/response data access, react‑i18next with **French as
default**. Mirrors the backend apps as `features/`.

> Before building UI, the implementing agent should consult the repository’s frontend design
> guidance (the `frontend-design` skill / design system) for typography, spacing and a non‑templated
> look. Use the PrimeReact **Lara** theme as the base and apply project branding in `app.scss`.

## 5.1 App shell & routing

`react-router-dom` v6. Routes are guarded by auth and capability. Layout = persistent **Topbar**
(project switcher, user menu, language switcher) + collapsible **Sidebar** (sections by domain) +
content area.

```
/login
/                         -> redirect to /dashboard
/dashboard                -> overview (summary cards + key Metabase embeds)
/indicators               -> result framework (PDO / intermediate / impact / execution tabs)
/indicators/:id           -> indicator detail (definition, targets, responsibilities, trend)
/measurements             -> measurement list + grid entry
/measurements/new         -> measurement form
/activities               -> activities list (filter by kind)
/activities/:kind/new     -> typed activity form (training, visit, meeting, subproject, ...)
/finance/budget           -> budget lines
/finance/transactions     -> financial transactions (engagements/disbursements/realisations)
/finance/dashboard        -> financial dashboards (Metabase embeds)
/procurement/ppm          -> procurement plan items
/procurement/processes    -> processes + stage tracking board
/procurement/dashboard    -> procurement dashboards
/grievances               -> MGP register + SLA dashboard
/impact                   -> impact monitoring (change tables t0/t1)
/reports                  -> generate/download quarterly & annual reports
/admin/geo                -> geography config (tree)
/admin/program            -> programme tree config
/admin/indicators         -> indicator/target/dimension config
/admin/reference          -> expense categories, funding sources, procurement methods/stages, grievance types, milestones
/admin/users              -> users, roles, role assignments (ADMIN)
/admin/responsibilities   -> the "Plan détaillé des rôles et responsabilités" matrix (view/export)
/profile                  -> current user profile & language preference
```

Guard: `<RequireAuth>` wraps the app; `<RequireCapability cap="…">` wraps admin/config routes.
Routes/sidebar items hidden when the user lacks the capability (from `/auth/me`).

## 5.2 Responsiveness (must work on a phone)

Field agents capture data on mobile, so this is a hard requirement.

- **Layout:** Bootstrap grid (`container-fluid`, `row`, `col-12 col-md-6 col-lg-4`). Sidebar
  collapses to an off‑canvas drawer (PrimeReact `Sidebar`) under `md`.
- **Tables:** PrimeReact `DataTable` in **responsiveLayout="stack"** with `breakpoint="960px"` so
  rows become stacked cards on small screens; expose the 3–5 most important columns on mobile, the
  rest behind a row‑expand. Always enable paginator, global search, and column filters on desktop.
- **Forms:** single column on mobile, two columns from `md`. Large tap targets; PrimeReact
  `InputNumber`, `Calendar` (touch‑friendly), `Dropdown`/`MultiSelect`.
- **Grid entry** (measurements): on desktop, an editable `DataTable` (one row per indicator/unit, a
  value cell + disaggregation cells). On mobile, fall back to a simple per‑indicator card form.
- **Charts:** Metabase embeds are responsive iframes (`width:100%`, aspect‑ratio box). Native summary
  cards reflow via the grid.
- Test at 360 px, 768 px, 1280 px.

## 5.3 The service layer (synchronous request/response)

`src/services/http.js` — a single axios instance:
- `baseURL = import.meta.env.VITE_API_BASE_URL` (e.g. `/api/v1`).
- Request interceptor: attach `Authorization: Bearer <access>` and `X-Project-Id: <currentProjectId>`.
- Response interceptor: on 401, try one refresh via `/auth/token/refresh/`, then retry; on repeated
  failure, log out. No request queues/polling beyond this single refresh‑retry.

`src/services/api/*.js` — one module per resource (`indicators.js`, `measurements.js`,
`activities.js`, `finance.js`, `procurement.js`, `grievances.js`, `reports.js`, `geo.js`,
`program.js`, `reference.js`, `users.js`, `dashboards.js`, `metabase.js`). Each exposes typed CRUD +
transition calls (e.g. `measurements.validate(id, {comment})`).

`src/services/hooks/*` — **TanStack Query** wrappers: `useIndicators(params)`, `useMeasurements(...)`,
mutations `useSubmitMeasurement()`, etc. Query keys include the current project id + filters.
Invalidate on mutation. Loading → spinner/skeleton; error → toast. (TanStack Query is pure
request/response caching — consistent with the “sync calls” requirement; no sockets.)

**Auth context** (`src/auth/AuthProvider.jsx`): holds access token (in memory) + refresh (in
`localStorage`), the `/auth/me` payload (user, roles, capabilities, projects, current project), and
`hasCapability(cap)` / `setCurrentProject(id)` helpers consumed across the app.

## 5.4 Reusable components (`src/components/`)

| Component | Built on | Purpose |
|---|---|---|
| `ListPage` | DataTable + Toolbar | Standard list scaffold: title, “New”, filters drawer, global search, paginator, export buttons (`xlsx`/`pdf`), responsive stack. |
| `EntityFormDialog` | Dialog + react‑hook‑form + zod | Create/edit modal; maps server field errors onto inputs. |
| `WorkflowBadge` | Tag | Renders `status` with colour + label (Brouillon/Soumis/Validé/Audité/Consolidé/Rejeté). |
| `WorkflowActions` | SplitButton + ConfirmDialog | Submit/Validate/Audit/Consolidate/Reject/Reopen buttons, shown per capability + current state; prompts for a comment; calls the transition API. |
| `StateTimeline` | Timeline | Renders `StateEvent` history + simple‑history diffs on a record. |
| `TreeSelectField` | TreeSelect | Pick a `GeoUnit` or `ProgramNode` from the configured tree. |
| `PeriodPicker` | Dropdown(s) | Year / quarter / month selector bound to project fiscal config. |
| `DisaggregationInputs` | InputNumber grid | Renders one numeric input per `DimensionCategory` of an indicator’s dimensions; live‑sums and warns vs total. |
| `RagIndicator` | custom | Green/amber/red dot + % for achievement vs target. |
| `MetabaseEmbed` | iframe | Fetches a signed URL from `/metabase/embed/` then renders a responsive iframe. |
| `KpiCard` | Card | Summary metric (value, target, RAG, sparkline optional). |
| `ProjectSwitcher` | Dropdown | Switch among the user’s projects (updates `X-Project-Id`, refetches). |
| `LanguageSwitcher` | Dropdown | fr/en via i18next. |
| `EmptyState` / `ErrorState` | Message | Consistent empty/error UX. |

## 5.5 Screen catalogue (what each page does)

### Dashboard (`/dashboard`)
- KPI cards for the 3 PDO indicators (value vs mid/closing target, RAG).
- Embedded Metabase **physical results** dashboard + **financial overview** (per capability).
- Quick links to data entry for the roles the user holds.

### Result framework (`/indicators`)
- Tabs: **ODP/PDO**, **Intermédiaires**, **Impact**, **Exécution**.
- Per tab, a `ListPage` of indicators grouped by component, with columns: code, name, unit, baseline,
  mid‑term, closing, latest value, achievement (RagIndicator). Click → detail.
- **Indicator detail:** definition (“Compréhension”), targets per milestone & geo, the
  **responsibilities** card (collecte/validation/audit/transfert/agrégation/analyse from
  `IndicatorResponsibility`), a trend chart of consolidated measurements, and the list of underlying
  measurements/activities.

### Measurements (`/measurements`)
- `ListPage` with filters (indicator, geo, period, status). `WorkflowBadge` per row;
  `WorkflowActions` inline + on detail.
- **Grid entry** mode: pick period + geo unit → editable DataTable of indicators with value +
  disaggregation cells → “Save all (draft)” → bulk POST. Then submit individually or in batch.
- New/edit form: indicator (searchable), geo unit (TreeSelect), period (PeriodPicker), value,
  `DisaggregationInputs`, narrative, attachments.

### Activities (`/activities`)
- Filter by `kind`. Typed forms per the Fiches:
  - **Training/Awareness:** theme, organizer, location, date, duration, total/women/youth, optional
    participant list (`ActivityParticipant` editable subtable), attachments.
  - **Field visit / Visit received:** date, location, object, observations/recommendations.
  - **Meeting:** date, location, participants (total/women), object, decisions.
  - **Sub‑project:** title, beneficiary org, management committee, objective, submission date,
    funding requested/obtained + dates, attachments.
  - **Stakeholder (autres intervenants):** name, implantation date, location, main actions.
  - **Observation note (changements observés):** geo, date, free narrative (+ attribution note).
- All carry `WorkflowBadge`/`WorkflowActions`.

### Finance
- **Budget lines** (`/finance/budget`): list/CRUD by component/category/geo/funding/year.
- **Transactions** (`/finance/transactions`): list/CRUD; `kind` tabs (Engagements / Décaissements /
  Réalisations); supporting‑doc upload required to consolidate a Réalisation; workflow actions.
- **Financial dashboard** (`/finance/dashboard`): embedded Metabase (by category, by component:
  budget vs disbursed vs realised, rates, reliquat) + native KpiCards as fallback.

### Procurement
- **PPM** (`/procurement/ppm`): plan items CRUD.
- **Processes** (`/procurement/processes`): list + a **stage board** (Kanban‑style columns =
  `ProcurementStage`; cards = processes) using PrimeReact `OrderList`/custom columns; “Advance stage”
  records start/end dates, decision, deadline. Detail shows stage durations (Tableau 5) and the
  monthly progress view (Tableau 6).
- **Procurement dashboard** (`/procurement/dashboard`): planned vs realised by category & method,
  in‑progress, average stage durations.

### Grievances (`/grievances`)
- Register (type, level, geo, channel, summary, complainant/anonymous, received date) → resolve/close
  /reject with notes; `is_within_sla` shown. SLA dashboard (by type/level/state, % within SLA).

### Impact (`/impact`)
- Per impact indicator, a **change table**: baseline (t0) / latest (t1) / change, by geo unit, from
  `v_impact_change`. Entry of impact measurements (often `source=SURVEY`/`IMPORT`).

### Reports (`/reports`)
- Pick template (Quarterly/Annual) + period → “Generate” (sync) → download PDF; list past reports;
  per‑tableau xlsx exports.

### Admin / configuration
- **Geo** (`/admin/geo`): manage `GeoLevel`s then the `GeoUnit` **tree** (add child, edit, populate
  population/coords). PRDC seed visible/editable.
- **Programme** (`/admin/program`): the component/sub‑component/action **tree**.
- **Indicators** (`/admin/indicators`): indicators, their dimensions, targets per milestone/geo,
  responsibilities.
- **Reference** (`/admin/reference`): expense categories, funding sources, procurement
  methods/stages, grievance types, milestones, report templates.
- **Users** (`/admin/users`): users, roles, `RoleAssignment` (with geo/program scope) — ADMIN only.
- **Responsibilities** (`/admin/responsibilities`): the manual’s annex matrix, read from
  `IndicatorResponsibility`, with xlsx/pdf export.

## 5.6 Internationalisation

- `react-i18next`; default `fr`, fallback `en`; detector reads user preference (`/auth/me`
  `default_locale`) then browser. All UI strings in `src/i18n/fr.json` / `en.json`.
- Domain data (indicator names, geo names) is shown as stored (French in the PRDC seed).
- Number/currency formatting from the project (`currency_symbol`); dates via `date-fns` with the `fr`
  locale by default.

## 5.7 Dashboard embedding mechanics

`MetabaseEmbed` component:
1. On mount, call `GET /api/v1/metabase/embed/?dashboard=<id>&...filters`.
2. Set the returned `iframe_url` as `<iframe src>` inside a responsive aspect‑ratio container.
3. Re‑fetch when filters (period/type/component) change — the backend re‑signs a token with the new
   **locked** params; project is always locked server‑side.
- Dashboard ids per environment come from config (the eight `VITE_MB_DASHBOARD_*` variables defined
  canonically in `06_dashboards_metabase.md` §6.5 — `…_RESULTS_PHYSICAL`, `…_RESULTS_FRAMEWORK`,
  `…_FINANCE_CATEGORY`, `…_FINANCE_COMPONENT`, `…_PROCUREMENT`, `…_GRIEVANCES`, `…_IMPACT`,
  `…_ACTIVITIES`) so a coding agent wires them after Metabase provisioning (see `06`).

## 5.8 Build/runtime config (`vite.config.js`, env)

- `VITE_API_BASE_URL=/api/v1`
- `VITE_MB_*` dashboard ids (the eight variables listed in `06_dashboards_metabase.md` §6.5)
- Dev proxy: Vite dev server proxies `/api` and `/metabase` to the local backend/Metabase so the SPA
  runs at `localhost:5173` against the compose stack.
- Production build (`npm run build`) → `dist/`, served by the frontend container’s nginx (SPA
  fallback to `index.html`).

## 5.9 Frontend phasing (summary; full plan in `08`)

- **Phase 1:** shell + auth + project switcher + i18n; admin config screens (geo, program,
  indicators, reference, users); measurements (list + grid entry + workflow); activities; dashboard
  with the physical‑results Metabase embed + PDO KpiCards.
- **Phase 2:** finance (budget, transactions, dashboard) and procurement (PPM, processes stage board,
  dashboard); reports (quarterly) UI; xlsx export buttons.
- **Phase 3:** grievances + SLA dashboard; impact change tables; annual report; responsibilities
  matrix screen; public/consultation read‑only mode; optional import wizard / custom forms UI.
