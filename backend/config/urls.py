from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from apps.accounts.views import (
    MeView,
    MetabaseEmbedView,
    RoleAssignmentViewSet,
    RoleViewSet,
    UserViewSet,
)

from apps.activities.views import (
    ActivityViewSet,
    TechnicalPlanViewSet,
    TechnicalScheduleViewSet,
    WorkPlanViewSet,
)

from apps.core.views import (
    ActorViewSet,
    AttachmentViewSet,
    AuditLogViewSet,
    MilestoneViewSet,
    PartnerViewSet,
    ProjectViewSet,
    UnitOfMeasureViewSet,
)

from apps.finance.views import (
    BudgetLineViewSet,
    ExpenseCategoryViewSet,
    FinancialTransactionViewSet,
    FundingSourceViewSet,
)

from apps.geo.views import (
    GeoLevelViewSet,
    GeoUnitViewSet,
)

from apps.grievances.views import (
    GrievanceTypeViewSet,
)

from apps.indicators.views import (
    DimensionCategoryViewSet,
    DimensionViewSet,
    IndicatorResponsibilityViewSet,
    IndicatorTargetViewSet,
    IndicatorTypeViewSet,
    IndicatorViewSet,
    MeasurementViewSet,
)

from apps.procurement.views import (
    PPMItemViewSet,
    ProcurementMethodViewSet,
    ProcurementProcessViewSet,
    ProcurementStageViewSet,
    StageEventViewSet,
)

from apps.program.views import (
    ProgramNodeViewSet,
)

from apps.reporting.views import (
    FinancialDashboard,
    IndicatorProgressDashboard,
    ProcurementDashboard,
    ReportTemplateViewSet,
    ReportViewSet,
)


# ======================================================================
# ROUTER API
# ======================================================================

router = DefaultRouter()


# ======================================================================
# CORE
# ======================================================================

router.register(
    "projects",
    ProjectViewSet,
    basename="project",
)

router.register(
    "milestones",
    MilestoneViewSet,
    basename="milestone",
)

router.register(
    "attachments",
    AttachmentViewSet,
    basename="attachment",
)

router.register(
    "units-of-measure",
    UnitOfMeasureViewSet,
    basename="unitofmeasure",
)

router.register(
    "actors",
    ActorViewSet,
    basename="actor",
)

router.register(
    "partners",
    PartnerViewSet,
    basename="partner",
)

router.register(
    "audit-logs",
    AuditLogViewSet,
    basename="auditlog",
)


# ======================================================================
# ACCOUNTS
# ======================================================================

router.register(
    "users",
    UserViewSet,
    basename="user",
)

router.register(
    "roles",
    RoleViewSet,
    basename="role",
)

router.register(
    "role-assignments",
    RoleAssignmentViewSet,
    basename="roleassignment",
)


# ======================================================================
# GEOGRAPHIE
# ======================================================================

router.register(
    "geo-levels",
    GeoLevelViewSet,
    basename="geolevel",
)

router.register(
    "geo-units",
    GeoUnitViewSet,
    basename="geounit",
)


# ======================================================================
# PROGRAMME
# ======================================================================

router.register(
    "program-nodes",
    ProgramNodeViewSet,
    basename="programnode",
)


# ======================================================================
# INDICATEURS
# ======================================================================

router.register(
    "indicator-types",
    IndicatorTypeViewSet,
    basename="indicatortype",
)

router.register(
    "dimensions",
    DimensionViewSet,
    basename="dimension",
)

router.register(
    "dimension-categories",
    DimensionCategoryViewSet,
    basename="dimensioncategory",
)

router.register(
    "indicators",
    IndicatorViewSet,
    basename="indicator",
)

router.register(
    "indicator-targets",
    IndicatorTargetViewSet,
    basename="indicatortarget",
)

router.register(
    "indicator-responsibilities",
    IndicatorResponsibilityViewSet,
    basename="indicatorresponsibility",
)

router.register(
    "measurements",
    MeasurementViewSet,
    basename="measurement",
)


# ======================================================================
# ACTIVITES / PTBA
# ======================================================================

# PTBA annuel
router.register(
    "workplans",
    WorkPlanViewSet,
    basename="workplan",
)

# Référentiel des activités
router.register(
    "activities",
    ActivityViewSet,
    basename="activity",
)

# Programmation technique annuelle
router.register(
    "technical-plans",
    TechnicalPlanViewSet,
    basename="technicalplan",
)

# Chronogramme mensuel
router.register(
    "technical-schedules",
    TechnicalScheduleViewSet,
    basename="technicalschedule",
)


# ======================================================================
# GRIEVANCES
# ======================================================================

# Reference data; record workflow is Phase 3
router.register(
    "grievance-types",
    GrievanceTypeViewSet,
    basename="grievancetype",
)


# ======================================================================
# FINANCE
# ======================================================================

router.register(
    "expense-categories",
    ExpenseCategoryViewSet,
    basename="expensecategory",
)

router.register(
    "funding-sources",
    FundingSourceViewSet,
    basename="fundingsource",
)

router.register(
    "budget-lines",
    BudgetLineViewSet,
    basename="budgetline",
)

router.register(
    "financial-transactions",
    FinancialTransactionViewSet,
    basename="financialtransaction",
)


# ======================================================================
# PASSATION DES MARCHES
# ======================================================================

router.register(
    "procurement-methods",
    ProcurementMethodViewSet,
    basename="procurementmethod",
)

router.register(
    "procurement-stages",
    ProcurementStageViewSet,
    basename="procurementstage",
)

router.register(
    "ppm-items",
    PPMItemViewSet,
    basename="ppmitem",
)

router.register(
    "procurement-processes",
    ProcurementProcessViewSet,
    basename="procurementprocess",
)

router.register(
    "stage-events",
    StageEventViewSet,
    basename="stageevent",
)


# ======================================================================
# REPORTING
# ======================================================================

router.register(
    "report-templates",
    ReportTemplateViewSet,
    basename="reporttemplate",
)

router.register(
    "reports",
    ReportViewSet,
    basename="report",
)


# ======================================================================
# API V1
# ======================================================================

api_v1 = [
    # ------------------------------------------------------------------
    # Authentification
    # ------------------------------------------------------------------

    path(
        "auth/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),

    path(
        "auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),

    path(
        "auth/me/",
        MeView.as_view(),
        name="me",
    ),

    # ------------------------------------------------------------------
    # Metabase
    # ------------------------------------------------------------------

    path(
        "metabase/embed/",
        MetabaseEmbedView.as_view(),
        name="metabase_embed",
    ),

    # ------------------------------------------------------------------
    # Dashboards
    # ------------------------------------------------------------------

    path(
        "dashboards/indicator-progress/",
        IndicatorProgressDashboard.as_view(),
        name="dash_indicator_progress",
    ),

    path(
        "dashboards/financial/",
        FinancialDashboard.as_view(),
        name="dash_financial",
    ),

    path(
        "dashboards/procurement/",
        ProcurementDashboard.as_view(),
        name="dash_procurement",
    ),

    # ------------------------------------------------------------------
    # Documentation API
    # ------------------------------------------------------------------

    path(
        "schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),

    path(
        "docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema"
        ),
        name="docs",
    ),

    # ------------------------------------------------------------------
    # Router DRF
    # ------------------------------------------------------------------

    path(
        "",
        include(router.urls),
    ),
]


# ======================================================================
# URLS PRINCIPALES
# ======================================================================

urlpatterns = [
    path(
        "admin/",
        admin.site.urls,
    ),

    path(
        "api/v1/",
        include(
            (api_v1, "api"),
            namespace="v1",
        ),
    ),
]


# ======================================================================
# MEDIA EN MODE DEBUG
# ======================================================================

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )