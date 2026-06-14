from django.db import connection
from django.utils import timezone
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import ReadOrCapability
from apps.core.api import AuthoredModelViewSet

from .models import Report, ReportTemplate
from .report_generation import generate_report_pdf
from .serializers import ReportSerializer, ReportTemplateSerializer


def dictfetch(sql, params):
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [c[0] for c in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


class _ProjectMixin:
    permission_classes = [IsAuthenticated]

    def project_id(self, request):
        project = getattr(request, "project", None)
        return project.id if project else None


class IndicatorProgressDashboard(_ProjectMixin, APIView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        pid = self.project_id(request)
        if not pid:
            return Response([], status=200)
        where = ["project_id = %s"]
        params = [pid]
        for key, column in (
            ("type", "indicator_type"),
            ("program_node", "program_node_id"),
            ("period_year", "period_year"),
        ):
            val = request.query_params.get(key)
            if val:
                where.append(f"{column} = %s")
                params.append(val)
        sql = f"SELECT * FROM v_indicator_progress WHERE {' AND '.join(where)}"
        return Response(dictfetch(sql, params))


class FinancialDashboard(_ProjectMixin, APIView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        pid = self.project_id(request)
        if not pid:
            return Response([], status=200)
        by = request.query_params.get("by", "category")
        view = "v_financial_by_component" if by == "component" else "v_financial_by_category"
        where = ["project_id = %s"]
        params = [pid]
        fy = request.query_params.get("fiscal_year")
        if fy:
            where.append("fiscal_year = %s")
            params.append(fy)
        sql = f"SELECT * FROM {view} WHERE {' AND '.join(where)}"
        return Response(dictfetch(sql, params))


class ProcurementDashboard(_ProjectMixin, APIView):
    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        pid = self.project_id(request)
        if not pid:
            return Response([], status=200)
        view = (
            "v_procurement_durations"
            if request.query_params.get("by") == "durations"
            else "v_procurement_status"
        )
        sql = f"SELECT * FROM {view} WHERE project_id = %s"
        return Response(dictfetch(sql, [pid]))


class ReportTemplateViewSet(AuthoredModelViewSet):
    serializer_class = ReportTemplateSerializer
    queryset = ReportTemplate.objects.all()
    permission_classes = [ReadOrCapability]
    write_capability = "config.manage"
    filterset_fields = ["code"]


class ReportViewSet(AuthoredModelViewSet):
    serializer_class = ReportSerializer
    queryset = Report.objects.select_related("template").all()
    permission_classes = [ReadOrCapability]
    write_capability = "report.generate"
    filterset_fields = ["template", "period_year", "period_quarter", "status"]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        report = serializer.save(
            project=self.request.project,
            created_by=user,
            updated_by=user,
            generated_by=user,
            generated_at=timezone.now(),
            status=Report.Status.FINAL,
        )
        generate_report_pdf(report)

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        from django.http import FileResponse, Http404

        report = self.get_object()
        if not report.file:
            raise Http404("No file generated for this report.")
        return FileResponse(report.file.open("rb"), as_attachment=True, filename=report.file.name)
