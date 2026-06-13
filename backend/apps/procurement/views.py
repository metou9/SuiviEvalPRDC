from datetime import date

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import ReadOrCapability, WorkflowObjectPermission
from apps.core.api import AuthoredModelViewSet, ExportMixin, WorkflowActionsMixin

from .models import (
    PPMItem,
    ProcurementMethod,
    ProcurementProcess,
    ProcurementStage,
    StageEvent,
)
from .serializers import (
    PPMItemSerializer,
    ProcurementMethodSerializer,
    ProcurementProcessSerializer,
    ProcurementStageSerializer,
    StageEventSerializer,
)


class ProcurementMethodViewSet(AuthoredModelViewSet):
    serializer_class = ProcurementMethodSerializer
    queryset = ProcurementMethod.objects.select_related("parent").all()
    permission_classes = [ReadOrCapability]
    write_capability = "config.manage"
    filterset_fields = {"parent": ["exact", "isnull"], "is_active": ["exact"]}
    search_fields = ["code", "name"]


class ProcurementStageViewSet(AuthoredModelViewSet):
    serializer_class = ProcurementStageSerializer
    queryset = ProcurementStage.objects.all()
    permission_classes = [ReadOrCapability]
    write_capability = "config.manage"
    ordering = ["order"]


class PPMItemViewSet(ExportMixin, AuthoredModelViewSet):
    serializer_class = PPMItemSerializer
    queryset = PPMItem.objects.select_related(
        "program_node", "expense_category", "procurement_method"
    ).all()
    permission_classes = [ReadOrCapability]
    write_capability = "procurementprocess.create"
    filterset_fields = ["program_node", "expense_category", "procurement_method", "planned_year", "is_active"]
    search_fields = ["ppm_ref", "designation"]


class StageEventViewSet(AuthoredModelViewSet):
    serializer_class = StageEventSerializer
    queryset = StageEvent.objects.select_related("procurement_stage", "procurement_process").all()
    permission_classes = [WorkflowObjectPermission]
    workflow_area = "procurementprocess"
    project_lookup = "procurement_process__project"
    filterset_fields = ["procurement_process", "procurement_stage"]

    def perform_create(self, serializer):
        serializer.save()


class ProcurementProcessViewSet(ExportMixin, WorkflowActionsMixin, AuthoredModelViewSet):
    serializer_class = ProcurementProcessSerializer
    queryset = ProcurementProcess.objects.select_related(
        "procurement_method", "expense_category", "program_node", "geo_unit", "current_stage", "ppm_item"
    ).prefetch_related("stage_events").all()
    permission_classes = [WorkflowObjectPermission]
    workflow_area = "procurementprocess"
    geo_scope_field = "geo_unit"
    filterset_fields = {
        "procurement_method": ["exact"],
        "expense_category": ["exact"],
        "program_node": ["exact"],
        "current_stage": ["exact"],
        "is_completed": ["exact"],
        "status": ["exact"],
    }
    search_fields = ["designation", "supplier"]

    @action(detail=True, methods=["post"])
    def advance(self, request, pk=None):
        """Close the current stage (end_date=today) and open the next (start_date=today)."""
        process = self.get_object()
        today = date.today()
        decision = request.data.get("decision", "")
        deadline = request.data.get("deadline") or None

        # Close the currently open stage event, if any.
        open_event = process.stage_events.filter(end_date__isnull=True).order_by(
            "-procurement_stage__order"
        ).first()
        if open_event:
            open_event.end_date = today
            if decision:
                open_event.decision = decision
            open_event.save()

        # Determine the next stage by order.
        current_order = process.current_stage.order if process.current_stage else -1
        next_stage = (
            ProcurementStage.objects.filter(project=process.project, order__gt=current_order)
            .order_by("order")
            .first()
        )
        if next_stage is None:
            process.is_completed = True
            process.save(update_fields=["is_completed", "updated_at"])
            return Response(
                {"detail": "Aucune étape suivante; processus marqué terminé.", "is_completed": True}
            )
        new_event = StageEvent.objects.create(
            procurement_process=process,
            procurement_stage=next_stage,
            start_date=today,
            deadline=deadline,
        )
        process.current_stage = next_stage
        process.save(update_fields=["current_stage", "updated_at"])
        return Response(
            {"detail": "Étape avancée.", "stage_event": StageEventSerializer(new_event).data}
        )
