from apps.accounts.permissions import WorkflowObjectPermission
from apps.core.api import AuthoredModelViewSet, ExportMixin, WorkflowActionsMixin

from .models import Activity
from .serializers import ActivitySerializer


class ActivityViewSet(
    ExportMixin,
    WorkflowActionsMixin,
    AuthoredModelViewSet
):
    serializer_class = ActivitySerializer

    queryset = (
        Activity.objects.select_related(
            "geo_unit",
            "program_node",
            "indicator",
            "workplan",
            "responsible",
        )
        .prefetch_related("participants")
        .all()
    )

    permission_classes = [WorkflowObjectPermission]

    workflow_area = "activity"
    geo_scope_field = "geo_unit"

    filterset_fields = {
        "workplan": ["exact"],
        "geo_unit": ["exact"],
        "program_node": ["exact"],
        "indicator": ["exact"],
        "responsible": ["exact"],
        "date": ["gte", "lte"],
    }

    search_fields = [
        "code",
        "title",
        "description",
        "organizer",
        "location",
        "expected_result",
    ]

    ordering_fields = [
        "code",
        "date",
        "created_at",
    ]

    ordering = ["-date"]

    # ?date_after / ?date_before convenience
    # maps to date__gte / date__lte
    def get_queryset(self):
        qs = super().get_queryset()

        after = self.request.query_params.get("date_after")
        before = self.request.query_params.get("date_before")

        if after:
            qs = qs.filter(date__gte=after)

        if before:
            qs = qs.filter(date__lte=before)

        return qs