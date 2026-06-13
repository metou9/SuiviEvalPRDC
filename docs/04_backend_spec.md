# 04 — Backend specification (Django + DRF)

Synchronous DRF. Custom user model from day one. Project‑scoped everything. OpenAPI via
`drf-spectacular`. This document is the contract the frontend agent codes against.

## 4.1 Django apps & responsibilities

| App | Models | Responsibility |
|---|---|---|
| `core` | `Project`, `Milestone`, `Attachment`, `StateEvent`; abstract `TimeStampedModel`, `AuthoredModel`, `WorkflowMixin` | Base classes, project entity, generic attachments, workflow engine, audit. |
| `accounts` | `User`, `Role`, `RoleAssignment`, `ProjectMembership` | Auth (SimpleJWT), capabilities, scoping, Metabase token endpoint, current‑project resolution. |
| `geo` | `GeoLevel`, `GeoUnit` | Configurable administrative hierarchy + tree helpers. |
| `program` | `ProgramNode` | Configurable programme tree. |
| `indicators` | `IndicatorType`, `Dimension`, `DimensionCategory`, `Indicator`, `IndicatorResponsibility`, `IndicatorDimension`, `IndicatorTarget`, `Measurement`, `MeasurementValue` | Result framework + the central measurement fact. |
| `activities` | `Activity`, `ActivityParticipant` | The Fiches (training, visit, meeting, sub‑project, stakeholder, observation). |
| `finance` | `ExpenseCategory`, `FundingSource`, `BudgetLine`, `FinancialTransaction` | Budget & financial realisation. |
| `procurement` | `ProcurementMethod`, `ProcurementStage`, `PPMItem`, `ProcurementProcess`, `StageEvent` | Passation de marchés. |
| `grievances` | `GrievanceType`, `Grievance` | MGP. |
| `reporting` | `ReportTemplate`, `Report`; SQL **views** as migrations; exporters | Reporting views, report generation, Excel/PDF exports. |

Each app: `models.py`, `serializers.py`, `views.py` (ViewSets), `permissions.py` (thin — delegate to
`accounts.has_capability`), `filters.py`, `urls.py`, `admin.py`, `tests/`. A `management/commands/`
in `core` (or a dedicated `seeds` app) holds `seed_reference` (generic, idempotent) and `seed_prdc`.

## 4.2 Settings essentials (`config/settings/base.py`)

```python
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework", "django_filters", "drf_spectacular", "corsheaders", "simple_history",
    "apps.core", "apps.accounts", "apps.geo", "apps.program", "apps.indicators",
    "apps.activities", "apps.finance", "apps.procurement", "apps.grievances", "apps.reporting",
]
AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "apps.accounts.middleware.CurrentProjectMiddleware",  # resolves X-Project-Id -> request.project
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

from datetime import timedelta
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}

SPECTACULAR_SETTINGS = {"TITLE": "M&E Platform API", "VERSION": "1.0.0",
                        "SERVE_INCLUDE_SCHEMA": False}

LANGUAGE_CODE = "fr"
LANGUAGES = [("fr", "Français"), ("en", "English")]
TIME_ZONE = "UTC"; USE_I18N = True; USE_TZ = True

# DB, CORS, Metabase, static read from env in dev.py / prod.py
```

`prod.py`: `DEBUG=False`, `ALLOWED_HOSTS` from env, secure cookie/HSTS settings, WhiteNoise compressed
storage, DB from env (`DATABASE_URL` or discrete vars), `CORS_ALLOWED_ORIGINS` from env,
`METABASE_SITE_URL` / `METABASE_EMBEDDING_SECRET` from env.

## 4.3 API conventions

- Base: `/api/v1/`. All list endpoints paginated, filterable, searchable, orderable.
- Every domain list endpoint **implicitly filters by `request.project`** (from `X-Project-Id`,
  validated against the user’s memberships). Cross‑project access is impossible via the API.
- Standard CRUD via `ModelViewSet`; workflow transitions via custom `@action` routes.
- Reference data exposed read+write to authorised config roles; read to everyone in project.

### 4.3.1 Auth & identity

| Method | Path | Purpose | Auth |
|---|---|---|---|
| POST | `/api/v1/auth/token/` | Obtain access+refresh | public |
| POST | `/api/v1/auth/token/refresh/` | Refresh access | refresh token |
| GET | `/api/v1/auth/me/` | Current user, roles, capabilities, memberships, default project | yes |
| GET | `/api/v1/projects/` | Projects the user may access | yes |
| POST | `/api/v1/projects/{id}/select/` | Set default project (optional convenience) | yes |
| GET | `/api/v1/metabase/embed/?dashboard=<n>&...` | Signed Metabase embed URL (see §4.6) | yes |

`/auth/me/` returns `{ id, username, display_name, default_locale, projects:[…],
roles:[{code,scope_geo,scope_program}], capabilities:[…] }` so the frontend can hide/show UI.

### 4.3.2 Configuration (reference data) — `IsAuthenticated` to read, `manage_config` to write

CRUD ViewSets at:
`/api/v1/milestones/`, `/api/v1/geo-levels/`, `/api/v1/geo-units/`, `/api/v1/program-nodes/`,
`/api/v1/indicator-types/`, `/api/v1/dimensions/`, `/api/v1/dimension-categories/`,
`/api/v1/indicators/`, `/api/v1/indicator-targets/`, `/api/v1/expense-categories/`,
`/api/v1/funding-sources/`, `/api/v1/procurement-methods/`, `/api/v1/procurement-stages/`,
`/api/v1/grievance-types/`, `/api/v1/report-templates/`, `/api/v1/roles/`, `/api/v1/users/`,
`/api/v1/role-assignments/`.

Useful filters/params:
- `geo-units`: `?level=<rank|code>`, `?parent=<id>`, `?tree=true` (returns nested), `?search=`.
- `program-nodes`: `?parent=<id>`, `?node_type=`, `?tree=true`.
- `indicators`: `?type=`, `?program_node=`, `?is_cri=`, `?is_active=`, `?search=`.
- `indicator-targets`: `?indicator=`, `?milestone=`, `?geo_unit=`.

### 4.3.3 Measurements — `/api/v1/measurements/`

- Filters: `?indicator=`, `?geo_unit=`, `?program_node=`, `?period_year=`, `?period_quarter=`,
  `?period_month=`, `?status=`, `?source=`.
- Nested write: `measurement_values:[{dimension_category, value}]` accepted in create/update.
- Transition actions: `submit/ validate/ audit/ consolidate/ reject/ reopen/` (POST, body `{comment}`).
- `GET /api/v1/measurements/{id}/history/` → field‑level history + `StateEvent` timeline.
- Bulk helper: `POST /api/v1/measurements/bulk/` accepts a list (one period, many indicators/units)
  to support fast grid entry from the frontend (still synchronous).

### 4.3.4 Activities — `/api/v1/activities/`

- Filters: `?kind=`, `?geo_unit=`, `?program_node=`, `?indicator=`, `?date_after=`, `?date_before=`,
  `?status=`.
- Nested `participants:[…]` accepted; `attachments` via the attachments endpoint (generic).
- Same transition actions as measurements.
- Convenience sub‑endpoints (thin wrappers with `kind` pre‑filtered) for the UI:
  `/api/v1/activities/trainings/`, `/visits/`, `/meetings/`, `/subprojects/`, `/stakeholders/`,
  `/observations/`.

### 4.3.5 Attachments — `/api/v1/attachments/`
- `multipart/form-data` upload; body `{content_type, object_id, file, label}`; list by `?content_type=&object_id=`.

### 4.3.6 Finance

- `/api/v1/budget-lines/` — filters `?program_node=&expense_category=&geo_unit=&funding_source=&fiscal_year=`.
- `/api/v1/financial-transactions/` — filters `?kind=&program_node=&expense_category=&geo_unit=&funding_source=&fiscal_year=&status=`; transition actions; `supporting_doc` required to consolidate a `REALIZATION`.

### 4.3.7 Procurement

- `/api/v1/ppm-items/` — filters `?program_node=&expense_category=&procurement_method=&planned_year=`.
- `/api/v1/procurement-processes/` — filters `?procurement_method=&expense_category=&program_node=&current_stage=&is_completed=&status=`; transition actions.
- `/api/v1/stage-events/` — nested under a process (`?process=`); create/advance a stage; `duration_days` read‑only computed.
- `POST /api/v1/procurement-processes/{id}/advance/` — convenience: closes the current stage
  (`end_date=today`) and opens the next (`start_date=today`), recording decision/deadline.

### 4.3.8 Grievances — `/api/v1/grievances/`
- Filters `?type=&geo_unit=&level=&state=&status=&received_after=&received_before=`.
- `POST /api/v1/grievances/{id}/resolve/` (sets `state=RESOLVED`, `resolved_at`, notes) and
  `…/close/`, `…/reject/`. `is_within_sla` computed.
- Data‑quality transitions (`submit/validate/…`) available too (the workflow `status`).

### 4.3.9 Reporting & exports

- `/api/v1/reports/` — list/create; `POST` body `{template, period_year, period_quarter?}` generates
  the report **synchronously** and returns the row with a `file` URL (PDF). See §4.7.
- `GET /api/v1/reports/{id}/download/` → the file.
- **Generic exports** (synchronous): any list endpoint accepts `?format=xlsx` (and where sensible
  `?format=pdf`) to stream an export of the current filtered query. Implemented by a shared
  `ExportMixin` using `openpyxl` (xlsx) / WeasyPrint (pdf).
- **Dashboard data endpoints** (server‑computed summaries that the SPA can render natively without
  Metabase, used for the in‑app summary cards and as a Metabase‑free fallback):
  - `GET /api/v1/dashboards/indicator-progress/?type=&program_node=&period_year=` → rows from
    `v_indicator_progress`.
  - `GET /api/v1/dashboards/financial/?by=category|component&fiscal_year=` → `v_financial_*`.
  - `GET /api/v1/dashboards/procurement/?by=category|method&year=` → `v_procurement_status`.
  - `GET /api/v1/dashboards/grievances/?period_year=` → `v_grievance_sla`.
  - `GET /api/v1/dashboards/impact/` → `v_impact_change`.
  These are **read‑only**, query the SQL views, and are also handy for tests.

## 4.4 Business logic — the calculations (the manual’s rates)

Centralise in `reporting/calculations.py` (used by the SQL views’ documentation and by the
`/dashboards/*` endpoints; the canonical computation lives in the SQL views, see `06`).

Definitions (per the manual §2.2.2):

- **Taux de réalisation physique** = `cumulative_realized / planned (target)` × 100. “Cumulative
  realized” is the indicator’s consolidated measurements rolled up by its `aggregation_method`
  (`SUM` for counts; `LAST`/`AVERAGE` for percentages/stocks). “Planned” is the relevant
  `IndicatorTarget` (default: the closing target; the UI can switch the reference milestone).
- **Taux de décaissement** = `sum(DISBURSEMENT) / budget` × 100, by category/component, life‑of‑project
  and for the current year.
- **Taux de réalisation financière** = `sum(REALIZATION) / budget` × 100 (only `REALIZATION` tx that
  are `CONSOLIDATED`, i.e. justified by supporting docs).
- **Reliquat / dépassement** = `budget − spent` (negative ⇒ dépassement/overrun).
- **Écarts** (variance): planned − realized, with the `narrative` field capturing explanatory
  factors and proposed solutions (the manual’s “Plan de gestion des difficultés”).
- **Cumulative + current period split**: every dashboard shows *cumul depuis le début du projet*,
  *année en cours*, *trimestre en cours*, *mois en cours* (Modèle 1). The views compute these from
  `period_year/quarter/month` relative to the requested current period.
- **RAG status** (traffic light): given `direction`, compare achievement to a configurable threshold
  (e.g. ≥90% green, 60–90% amber, <60% red for INCREASE indicators; inverse for DECREASE). Threshold
  constants in `reporting/calculations.py`.
- **Procurement realisation rate** = `realised_count / planned_count` (and amount equivalents) by
  category and by method; **stage duration** = `end_date − start_date` per stage.
- **Grievance SLA %** = `resolved_within_sla / total_resolved` (or of total received, configurable).

> The **link cost↔result** the manual requires is achieved by joining `FinancialTransaction` and
> `Measurement`/`Activity` on `program_node` (+ `geo_unit` + period) — same nomenclature/codification
> on both sides, which is exactly why `ProgramNode` and `ExpenseCategory` are shared reference data.

## 4.5 Serializers & validation notes

- Reference serializers expose `code`, `name`, and nested children for tree endpoints (`?tree=true`).
- `MeasurementSerializer`: validates that submitted `measurement_values` reference dimension
  categories of dimensions linked to the indicator; warns (non‑blocking) if disaggregated sum ≠
  `value`.
- `FinancialTransactionSerializer`: enforces `supporting_doc` present before a `REALIZATION` can be
  consolidated (validated in the `consolidate` action, not on create).
- `GeoUnitSerializer`: validates parent level rank = own rank − 1.
- All transition actions check `has_capability(user, '<area>.<step>', obj)` and record a `StateEvent`.

## 4.6 Metabase signed‑embed token endpoint (sync, OSS‑compatible)

`GET /api/v1/metabase/embed/?dashboard=<id>&<param>=<value>...`

```python
import time, jwt
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response

class MetabaseEmbedView(APIView):
    def get(self, request):
        dashboard_id = int(request.query_params["dashboard"])
        # locked params: always lock to the current project; pass through whitelisted filters
        params = {"project_id": request.project.id}
        for key in ("fiscal_year", "indicator_type", "program_node", "status"):
            if key in request.query_params:
                params[key] = request.query_params[key]
        payload = {
            "resource": {"dashboard": dashboard_id},
            "params": params,
            "exp": round(time.time()) + 10 * 60,  # 10‑minute token
        }
        token = jwt.encode(payload, settings.METABASE_EMBEDDING_SECRET, algorithm="HS256")
        url = (f"{settings.METABASE_SITE_URL}/embed/dashboard/{token}"
               f"#bordered=false&titled=false&theme=light")
        return Response({"iframe_url": url})
```

- `METABASE_EMBEDDING_SECRET` is the **Embedding** secret key from Metabase Admin → Embedding
  (static embedding enabled). `METABASE_SITE_URL` is the externally reachable Metabase base
  (`https://<host>/metabase`).
- **Locking `project_id`** (and `status` for public) server‑side guarantees a user can only ever see
  their project’s consolidated data, regardless of what the iframe tries.
- The frontend calls this endpoint, then sets the returned `iframe_url` as the `<iframe src>`.
- This uses **only the OSS static‑embedding** feature (no Pro/Enterprise license needed).

## 4.7 Report generation (synchronous)

`reporting` builds the **quarterly** and **annual** reports described in the manual (§2.3.6):
*rappel des objectifs du trimestre, résultats physiques & financiers par composante, situation
passation de marchés, plan de gestion des difficultés, annexes (tableaux de bord)*.

- A `ReportTemplate.structure` JSON lists sections; the generator renders an HTML template per
  section (Django templates) pulling from the reporting views for the requested period, then
  WeasyPrint → PDF. Generation happens in‑request (small data); for very large annexes the response
  streams. Output stored on `Report.file` and downloadable.
- Also offer `?format=xlsx` workbook variants of the dashboards (one sheet per tableau de bord:
  physical results, financial by category, financial by component, procurement, grievances).

## 4.8 Testing (pytest + `pytest-django`)

- **Model/state‑machine tests:** every legal transition succeeds for an authorised+in‑scope user and
  fails otherwise; illegal transitions raise; `StateEvent` written.
- **Permission/scope tests:** matrix‑driven — for each role, assert allowed/denied per capability;
  geo‑scope filtering hides out‑of‑scope records.
- **Calculation tests:** seed known measurements/budgets and assert the rate outputs (physical,
  disbursement, financial realisation, cumulative vs current period, RAG).
- **API contract tests:** list filters, pagination, nested writes, export endpoints return files,
  Metabase embed returns a well‑formed signed URL (decode + verify locked `project_id`).
- **Seed test:** `seed_prdc` is idempotent (run twice → no duplicates) and produces the expected
  counts (17 communes, 4 components + 7 sub‑components, ≥20 indicators, 6 expense categories, 6
  procurement methods incl. sub‑methods, 5 stages).

## 4.9 Backend phasing (summary; full plan in `08`)

- **Phase 1:** `core`, `accounts` (auth, roles, scoping, capabilities, workflow engine), `geo`,
  `program`, `indicators` (incl. `Measurement` + transitions), `activities`, `seed_reference`/
  `seed_prdc`, OpenAPI, the `/dashboards/indicator-progress/` endpoint + `v_indicator_progress`
  view, Metabase embed endpoint.
- **Phase 2:** `finance`, `procurement`, financial & procurement views + dashboard endpoints,
  report generation (quarterly), generic xlsx export.
- **Phase 3:** `grievances`, impact handling (impact indicators already modelled; add `v_impact_change`
  and impact entry conveniences), annual report, public/consultation embeds, optional CSV/Kobo import
  endpoint, optional `IndicatorComputation` auto‑derivation, optional custom forms.
