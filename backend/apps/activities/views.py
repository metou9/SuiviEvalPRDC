from rest_framework.decorators import action

from apps.accounts.permissions import WorkflowObjectPermission
from apps.core.api import AuthoredModelViewSet, ExportMixin, WorkflowActionsMixin

from .models import Activity
from .serializers import ActivitySerializer


def _kind_action(name, kind):
    @action(detail=False, methods=["get"], url_path=name)
    def _list(self, request):
        qs = self.filter_queryset(self.get_queryset().filter(kind=kind))
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page if page is not None else qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        from rest_framework.response import Response

        return Response(serializer.data)

    _list.__name__ = name
    return _list


class ActivityViewSet(ExportMixin, WorkflowActionsMixin, AuthoredModelViewSet):
    serializer_class = ActivitySerializer
    queryset = (
        Activity.objects.select_related("geo_unit", "program_node", "indicator")
        .prefetch_related("participants")
        .all()
    )
    permission_classes = [WorkflowObjectPermission]
    workflow_area = "activity"
    geo_scope_field = "geo_unit"
    filterset_fields = {
        "kind": ["exact"],
        "geo_unit": ["exact"],
        "program_node": ["exact"],
        "indicator": ["exact"],
        "status": ["exact"],
        "date": ["gte", "lte"],
    }
    search_fields = ["title", "description", "organizer", "location"]
    ordering_fields = ["date", "created_at"]
    ordering = ["-date"]

    # ?date_after / ?date_before convenience (maps to date__gte / date__lte)
    def get_queryset(self):
        qs = super().get_queryset()
        after = self.request.query_params.get("date_after")
        before = self.request.query_params.get("date_before")
        if after:
            qs = qs.filter(date__gte=after)
        if before:
            qs = qs.filter(date__lte=before)
        return qs

    trainings = _kind_action("trainings", Activity.Kind.TRAINING)
    visits = _kind_action("visits", Activity.Kind.FIELD_VISIT)
    meetings = _kind_action("meetings", Activity.Kind.MEETING)
    subprojects = _kind_action("subprojects", Activity.Kind.SUBPROJECT)
    stakeholders = _kind_action("stakeholders", Activity.Kind.STAKEHOLDER)
    observations = _kind_action("observations", Activity.Kind.OBSERVATION)
