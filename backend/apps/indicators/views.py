from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import ReadOrCapability, WorkflowObjectPermission
from apps.core.api import AuthoredModelViewSet, ExportMixin, WorkflowActionsMixin

from .models import (
    Dimension,
    DimensionCategory,
    Indicator,
    IndicatorResponsibility,
    IndicatorTarget,
    IndicatorType,
    Measurement,
)
from .serializers import (
    DimensionCategorySerializer,
    DimensionSerializer,
    IndicatorResponsibilitySerializer,
    IndicatorSerializer,
    IndicatorTargetSerializer,
    IndicatorTypeSerializer,
    MeasurementSerializer,
)


class IndicatorTypeViewSet(AuthoredModelViewSet):
    serializer_class = IndicatorTypeSerializer
    queryset = IndicatorType.objects.all()
    permission_classes = [ReadOrCapability]
    write_capability = "config.manage"
    filterset_fields = ["code"]
    ordering = ["order"]


class DimensionViewSet(AuthoredModelViewSet):
    serializer_class = DimensionSerializer
    queryset = Dimension.objects.prefetch_related("categories").all()
    permission_classes = [ReadOrCapability]
    write_capability = "config.manage"
    filterset_fields = ["code", "is_active"]
    search_fields = ["code", "name"]


class DimensionCategoryViewSet(AuthoredModelViewSet):
    serializer_class = DimensionCategorySerializer
    queryset = DimensionCategory.objects.select_related("dimension").all()
    permission_classes = [ReadOrCapability]
    write_capability = "config.manage"
    project_lookup = "dimension__project"
    filterset_fields = ["dimension"]


class IndicatorViewSet(ExportMixin, AuthoredModelViewSet):
    serializer_class = IndicatorSerializer
    queryset = (
        Indicator.objects.select_related("indicator_type", "program_node")
        .prefetch_related("responsibilities", "targets")
        .all()
    )
    permission_classes = [ReadOrCapability]
    write_capability = "config.manage"
    filterset_fields = {
        "indicator_type": ["exact"],
        "program_node": ["exact"],
        "is_cri": ["exact"],
        "is_active": ["exact"],
    }
    search_fields = ["code", "name", "definition"]
    ordering_fields = ["order", "code"]

    def get_queryset(self):
        qs = super().get_queryset()
        type_code = self.request.query_params.get("type")
        if type_code:
            qs = qs.filter(indicator_type__code=type_code)
        return qs


class IndicatorTargetViewSet(AuthoredModelViewSet):
    serializer_class = IndicatorTargetSerializer
    queryset = IndicatorTarget.objects.select_related("milestone", "indicator").all()
    permission_classes = [ReadOrCapability]
    write_capability = "config.manage"
    project_lookup = "indicator__project"
    filterset_fields = ["indicator", "milestone", "geo_unit"]


class IndicatorResponsibilityViewSet(AuthoredModelViewSet):
    serializer_class = IndicatorResponsibilitySerializer
    queryset = IndicatorResponsibility.objects.select_related("role", "user", "indicator").all()
    permission_classes = [ReadOrCapability]
    write_capability = "config.manage"
    project_lookup = "indicator__project"
    filterset_fields = ["indicator", "responsibility"]


class MeasurementViewSet(ExportMixin, WorkflowActionsMixin, AuthoredModelViewSet):
    serializer_class = MeasurementSerializer
    queryset = (
        Measurement.objects.select_related("indicator", "geo_unit", "program_node")
        .prefetch_related("measurement_values")
        .all()
    )
    permission_classes = [WorkflowObjectPermission]
    workflow_area = "measurement"
    geo_scope_field = "geo_unit"
    filterset_fields = {
        "indicator": ["exact"],
        "geo_unit": ["exact"],
        "program_node": ["exact"],
        "period_year": ["exact"],
        "period_quarter": ["exact"],
        "period_month": ["exact"],
        "status": ["exact"],
        "source": ["exact"],
    }
    search_fields = ["indicator__code", "indicator__name", "narrative"]
    ordering_fields = ["period_year", "period_quarter", "value", "created_at"]
    ordering = ["-period_year", "-period_quarter"]

    @action(detail=False, methods=["post"])
    def bulk(self, request):
        """Create many measurements in one synchronous call (fast grid entry)."""
        data = request.data
        if not isinstance(data, list):
            return Response({"detail": "expected a list"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        user = request.user if request.user.is_authenticated else None
        serializer.save(project=request.project, created_by=user, updated_by=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
