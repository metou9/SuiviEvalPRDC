"""Shared DRF building blocks: project scoping, workflow actions, exports."""
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import StateEvent, WorkflowError


class ProjectScopedQuerysetMixin:
    """Filters every queryset to ``request.project`` and (optionally) geo scope.

    Set ``geo_scope_field`` on the viewset to the name of the geo-unit FK to apply
    geographic scoping from the user's role assignments.
    """
    geo_scope_field = None
    project_lookup = "project"  # ORM path from the model to its Project

    def get_queryset(self):
        qs = super().get_queryset()
        project = getattr(self.request, "project", None)
        if not project:
            return qs.none()
        qs = qs.filter(**{self.project_lookup: project})
        if self.geo_scope_field:
            from apps.accounts.capabilities import accessible_geo_unit_ids

            allowed = accessible_geo_unit_ids(self.request.user, project)
            if allowed is not None:
                # Keep rows in scope OR rows with no geo unit (project-wide).
                qs = qs.filter(
                    models_q_geo(self.geo_scope_field, allowed)
                )
        return qs


def models_q_geo(field, allowed_ids):
    from django.db.models import Q

    return Q(**{f"{field}__in": allowed_ids}) | Q(**{f"{field}__isnull": True})


class AuthoredModelViewSet(ProjectScopedQuerysetMixin, viewsets.ModelViewSet):
    """ModelViewSet that stamps project + audit fields on write."""

    def perform_create(self, serializer):
        kwargs = {}
        # Only set project for project-owned models.
        if any(f.name == "project" for f in serializer.Meta.model._meta.fields):
            kwargs["project"] = self.request.project
        user = self.request.user if self.request.user.is_authenticated else None
        if any(f.name == "created_by" for f in serializer.Meta.model._meta.fields):
            kwargs["created_by"] = user
            kwargs["updated_by"] = user
        serializer.save(**kwargs)

    def perform_update(self, serializer):
        kwargs = {}
        user = self.request.user if self.request.user.is_authenticated else None
        if any(f.name == "updated_by" for f in serializer.Meta.model._meta.fields):
            kwargs["updated_by"] = user
        serializer.save(**kwargs)


class WorkflowActionsMixin:
    """Adds the six transition actions + a history endpoint to a ModelViewSet."""

    def _do_transition(self, request, action_name):
        obj = self.get_object()
        comment = request.data.get("comment", "")
        try:
            event = obj.transition(request.user, action_name, comment=comment)
        except WorkflowError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        data = self.get_serializer(obj).data
        return Response(
            {
                "record": data,
                "state_event": {
                    "from_state": event.from_state,
                    "to_state": event.to_state,
                    "action": event.action,
                    "at": event.at,
                    "comment": event.comment,
                },
            }
        )

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        return self._do_transition(request, "submit")

    @action(detail=True, methods=["post"])
    def validate(self, request, pk=None):
        return self._do_transition(request, "validate")

    @action(detail=True, methods=["post"])
    def audit(self, request, pk=None):
        return self._do_transition(request, "audit")

    @action(detail=True, methods=["post"])
    def consolidate(self, request, pk=None):
        return self._do_transition(request, "consolidate")

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._do_transition(request, "reject")

    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        return self._do_transition(request, "reopen")

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        obj = self.get_object()
        ct = ContentType.objects.get_for_model(obj.__class__)
        events = StateEvent.objects.filter(content_type=ct, object_id=obj.pk)
        timeline = [
            {
                "from_state": e.from_state,
                "to_state": e.to_state,
                "action": e.action,
                "actor": getattr(e.actor, "username", None),
                "at": e.at,
                "comment": e.comment,
            }
            for e in events
        ]
        return Response({"timeline": timeline})


class ExportMixin:
    """Adds ``?format=xlsx`` streaming export of the current filtered list."""

    export_columns = None  # list of (header, attr) tuples; defaults to serializer fields

    def list(self, request, *args, **kwargs):
        if request.query_params.get("format") == "xlsx":
            return self._export_xlsx(request)
        return super().list(request, *args, **kwargs)

    def _export_xlsx(self, request):
        from openpyxl import Workbook

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        rows = serializer.data
        wb = Workbook()
        ws = wb.active
        ws.title = "export"
        if rows:
            headers = list(rows[0].keys())
            ws.append(headers)
            for row in rows:
                ws.append([_flatten(row.get(h)) for h in headers])
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="export.xlsx"'
        wb.save(response)
        return response


def _flatten(value):
    if isinstance(value, (list, dict)):
        return str(value)
    return value
