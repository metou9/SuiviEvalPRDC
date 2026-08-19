from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import (
    MeView,
    MetabaseEmbedView,
    RoleAssignmentViewSet,
    RoleViewSet,
    UserViewSet,
)
from apps.activities.views import ActivityViewSet
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
from apps.geo.views import GeoLevelViewSet, GeoUnitViewSet
from apps.grievances.views import GrievanceTypeViewSet
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
from apps.program.views import ProgramNodeViewSet
from apps.reporting.views import (
    FinancialDashboard,
    IndicatorProgressDashboard,
    ProcurementDashboard,
    ReportTemplateViewSet,
    ReportViewSet,
)

router = DefaultRouter()
# core
router.register("projects", ProjectViewSet, basename="project")
router.register("milestones", MilestoneViewSet, basename="milestone")
router.register("attachments", AttachmentViewSet, basename="attachment")
router.register("units-of-measure", UnitOfMeasureViewSet, basename="unitofmeasure")
router.register("actors", ActorViewSet, basename="actor")
router.register("partners", PartnerViewSet, basename="partner")
router.register("audit-logs", AuditLogViewSet, basename="auditlog")
# accounts
router.register("users", UserViewSet, basename="user")
router.register("roles", RoleViewSet, basename="role")
router.register("role-assignments", RoleAssignmentViewSet, basename="roleassignment")
# geo
router.register("geo-levels", GeoLevelViewSet, basename="geolevel")
router.register("geo-units", GeoUnitViewSet, basename="geounit")
# program
router.register("program-nodes", ProgramNodeViewSet, basename="programnode")
# indicators
router.register("indicator-types", IndicatorTypeViewSet, basename="indicatortype")
router.register("dimensions", DimensionViewSet, basename="dimension")
router.register("dimension-categories", DimensionCategoryViewSet, basename="dimensioncategory")
router.register("indicators", IndicatorViewSet, basename="indicator")
router.register("indicator-targets", IndicatorTargetViewSet, basename="indicatortarget")
router.register(
    "indicator-responsibilities", IndicatorResponsibilityViewSet, basename="indicatorresponsibility"
)
router.register("measurements", MeasurementViewSet, basename="measurement")
# activities
router.register("activities", ActivityViewSet, basename="activity")
# grievances (reference data; record workflow is Phase 3)
router.register("grievance-types", GrievanceTypeViewSet, basename="grievancetype")
# finance
router.register("expense-categories", ExpenseCategoryViewSet, basename="expensecategory")
router.register("funding-sources", FundingSourceViewSet, basename="fundingsource")
router.register("budget-lines", BudgetLineViewSet, basename="budgetline")
router.register(
    "financial-transactions", FinancialTransactionViewSet, basename="financialtransaction"
)
# procurement
router.register("procurement-methods", ProcurementMethodViewSet, basename="procurementmethod")
router.register("procurement-stages", ProcurementStageViewSet, basename="procurementstage")
router.register("ppm-items", PPMItemViewSet, basename="ppmitem")
router.register(
    "procurement-processes", ProcurementProcessViewSet, basename="procurementprocess"
)
router.register("stage-events", StageEventViewSet, basename="stageevent")
# reporting
router.register("report-templates", ReportTemplateViewSet, basename="reporttemplate")
router.register("reports", ReportViewSet, basename="report")

api_v1 = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("metabase/embed/", MetabaseEmbedView.as_view(), name="metabase_embed"),
    path(
        "dashboards/indicator-progress/",
        IndicatorProgressDashboard.as_view(),
        name="dash_indicator_progress",
    ),
    path("dashboards/financial/", FinancialDashboard.as_view(), name="dash_financial"),
    path("dashboards/procurement/", ProcurementDashboard.as_view(), name="dash_procurement"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("", include(router.urls)),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include((api_v1, "api"), namespace="v1")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
