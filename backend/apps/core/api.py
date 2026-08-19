"""Shared DRF building blocks: project scoping, workflow actions, exports."""

from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AuditLog, StateEvent, WorkflowError


class ProjectScopedQuerysetMixin:
    """Filters every queryset to `request.project` and (optionally) geo scope.

    Set ``geo_scope_field`` on the viewset to the name of the geo-unit FK to apply
    geographic scoping from the user's role assignments.
    """

    geo_scope_field = None
    project_lookup = "project"

    def get_queryset(self):
        qs = super().get_queryset()

        project = getattr(self.request, "project", None)

        if not project:
            return qs.none()

        qs = qs.filter(
            **{self.project_lookup: project}
        )

        if self.geo_scope_field:
            from apps.accounts.capabilities import accessible_geo_unit_ids

            allowed = accessible_geo_unit_ids(
                self.request.user,
                project,
            )

            if allowed is not None:
                qs = qs.filter(
                    models_q_geo(
                        self.geo_scope_field,
                        allowed,
                    )
                )

        return qs


def models_q_geo(field, allowed_ids):
    from django.db.models import Q

    return (
        Q(**{f"{field}__in": allowed_ids})
        | Q(**{f"{field}__isnull": True})
    )


class AuthoredModelViewSet(
    ProjectScopedQuerysetMixin,
    viewsets.ModelViewSet,
):
    """ModelViewSet that stamps project + author fields and records CRUD audit."""

    # ------------------------------------------------------------------
    # Audit helpers
    # ------------------------------------------------------------------

    def _audit_value(self, value):
        """
        Convert model values to values safely storable in JSONField.
        """

        if value is None:
            return None

        if isinstance(value, (str, int, float, bool)):
            return value

        return str(value)

    def _snapshot(self, instance):
        """
        Capture concrete model fields before/after a modification.

        Foreign keys are stored using their *_id value so the audit
        does not depend on the related object still existing later.
        """

        data = {}

        ignored_fields = {
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        }

        for field in instance._meta.concrete_fields:
            if field.name in ignored_fields:
                continue

            value = getattr(
                instance,
                field.attname,
                None,
            )

            data[field.name] = self._audit_value(value)

        return data

    def _write_audit(
        self,
        instance,
        action,
        changes=None,
        object_id=None,
        object_repr=None,
        project=None,
        content_type=None,
    ):
        """
        Write one generic CRUD audit record.
        """

        user = (
            self.request.user
            if self.request.user.is_authenticated
            else None
        )

        if project is None:
            project = getattr(
                instance,
                "project",
                None,
            )

        if project is None:
            project = getattr(
                self.request,
                "project",
                None,
            )

        if content_type is None:
            content_type = ContentType.objects.get_for_model(
                instance.__class__
            )

        if object_id is None:
            object_id = getattr(
                instance,
                "pk",
                None,
            )

        if object_repr is None:
            object_repr = str(instance)

        AuditLog.objects.create(
            project=project,
            content_type=content_type,
            object_id=object_id,
            object_repr=object_repr,
            action=action,
            actor=user,
            changes=changes or {},
        )

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def perform_create(self, serializer):
        kwargs = {}

        model = serializer.Meta.model

        # Only set project for project-owned models.
        if any(
            f.name == "project"
            for f in model._meta.fields
        ):
            kwargs["project"] = self.request.project

        user = (
            self.request.user
            if self.request.user.is_authenticated
            else None
        )

        if any(
            f.name == "created_by"
            for f in model._meta.fields
        ):
            kwargs["created_by"] = user
            kwargs["updated_by"] = user

        instance = serializer.save(
            **kwargs
        )

        self._write_audit(
            instance,
            AuditLog.Action.CREATE,
            changes={
                "after": self._snapshot(instance),
            },
        )

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    def perform_update(self, serializer):
        instance = serializer.instance

        before = self._snapshot(
            instance
        )

        kwargs = {}

        user = (
            self.request.user
            if self.request.user.is_authenticated
            else None
        )

        if any(
            f.name == "updated_by"
            for f in serializer.Meta.model._meta.fields
        ):
            kwargs["updated_by"] = user

        instance = serializer.save(
            **kwargs
        )

        after = self._snapshot(
            instance
        )

        changes = {}

        all_fields = set(before) | set(after)

        for field_name in all_fields:
            old_value = before.get(
                field_name
            )

            new_value = after.get(
                field_name
            )

            if old_value != new_value:
                changes[field_name] = {
                    "before": old_value,
                    "after": new_value,
                }

        self._write_audit(
            instance,
            AuditLog.Action.UPDATE,
            changes=changes,
        )

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def perform_destroy(self, instance):
        before = self._snapshot(
            instance
        )

        object_id = instance.pk
        object_repr = str(instance)

        project = getattr(
            instance,
            "project",
            None,
        )

        if project is None:
            project = getattr(
                self.request,
                "project",
                None,
            )

        content_type = ContentType.objects.get_for_model(
            instance.__class__
        )

        instance.delete()

        self._write_audit(
            instance,
            AuditLog.Action.DELETE,
            changes={
                "before": before,
            },
            object_id=object_id,
            object_repr=object_repr,
            project=project,
            content_type=content_type,
        )


class WorkflowActionsMixin:
    """Adds the six transition actions + a history endpoint to a ModelViewSet."""

    def _do_transition(self, request, action_name):
        obj = self.get_object()
        comment = request.data.get(
            "comment",
            "",
        )

        try:
            event = obj.transition(
                request.user,
                action_name,
                comment=comment,
            )

        except WorkflowError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = self.get_serializer(
            obj
        ).data

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
        return self._do_transition(
            request,
            "submit",
        )

    @action(detail=True, methods=["post"])
    def validate(self, request, pk=None):
        return self._do_transition(
            request,
            "validate",
        )

    @action(detail=True, methods=["post"])
    def audit(self, request, pk=None):
        return self._do_transition(
            request,
            "audit",
        )

    @action(detail=True, methods=["post"])
    def consolidate(self, request, pk=None):
        return self._do_transition(
            request,
            "consolidate",
        )

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._do_transition(
            request,
            "reject",
        )

    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        return self._do_transition(
            request,
            "reopen",
        )

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        obj = self.get_object()

        ct = ContentType.objects.get_for_model(
            obj.__class__
        )

        events = StateEvent.objects.filter(
            content_type=ct,
            object_id=obj.pk,
        )

        timeline = [
            {
                "from_state": e.from_state,
                "to_state": e.to_state,
                "action": e.action,
                "actor": getattr(
                    e.actor,
                    "username",
                    None,
                ),
                "at": e.at,
                "comment": e.comment,
            }
            for e in events
        ]

        return Response(
            {
                "timeline": timeline
            }
        )


class ExportMixin:
    """Adds `?format=xlsx` streaming export of the current filtered list."""

    export_columns = None

    def list(self, request, *args, **kwargs):
        if request.query_params.get("format") == "xlsx":
            return self._export_xlsx(
                request
            )

        return super().list(
            request,
            *args,
            **kwargs
        )

    def _export_xlsx(self, request):
        from openpyxl import Workbook

        queryset = self.filter_queryset(
            self.get_queryset()
        )

        serializer = self.get_serializer(
            queryset,
            many=True,
        )

        rows = serializer.data

        wb = Workbook()
        ws = wb.active
        ws.title = "export"

        if rows:
            headers = list(
                rows[0].keys()
            )

            ws.append(
                headers
            )

            for row in rows:
                ws.append(
                    [
                        _flatten(
                            row.get(h)
                        )
                        for h in headers
                    ]
                )

        response = HttpResponse(
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )
        )

        response[
            "Content-Disposition"
        ] = 'attachment; filename="export.xlsx"'

        wb.save(
            response
        )

        return response


def _flatten(value):
    if isinstance(
        value,
        (list, dict),
    ):
        return str(value)

    return value