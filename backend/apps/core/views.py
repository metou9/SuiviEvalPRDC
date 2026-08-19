from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import ReadOrCapability
from .api import AuthoredModelViewSet, ProjectScopedQuerysetMixin
from .models import (
    Actor,
    Attachment,
    AuditLog,
    Milestone,
    Partner,
    Project,
    UnitOfMeasure,
)
from .serializers import (
    ActorSerializer,
    AttachmentSerializer,
    AuditLogSerializer,
    MilestoneSerializer,
    PartnerSerializer,
    ProjectSerializer,
    UnitOfMeasureSerializer,
)


class ProjectViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Projects the current user may access (via ProjectMembership)."""

    serializer_class = ProjectSerializer

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Project.objects.none()

        if user.is_superuser:
            return Project.objects.all()

        return Project.objects.filter(
            memberships__user=user
        ).distinct()

    @action(detail=True, methods=["post"])
    def select(self, request, pk=None):
        """Mark this project as the user's default."""

        from apps.accounts.models import ProjectMembership

        project = self.get_object()

        ProjectMembership.objects.filter(
            user=request.user
        ).update(
            is_default=False
        )

        ProjectMembership.objects.filter(
            user=request.user,
            project=project,
        ).update(
            is_default=True
        )

        return Response(
            {
                "detail": "default project updated",
                "project": project.id,
            }
        )


class MilestoneViewSet(AuthoredModelViewSet):
    serializer_class = MilestoneSerializer
    queryset = Milestone.objects.all()
    filterset_fields = ["code"]
    search_fields = ["code", "name"]
    ordering_fields = ["order", "target_date"]
    ordering = ["order"]


class AttachmentViewSet(AuthoredModelViewSet):
    serializer_class = AttachmentSerializer
    queryset = Attachment.objects.all()
    filterset_fields = [
        "content_type",
        "object_id",
    ]


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

class UnitOfMeasureViewSet(AuthoredModelViewSet):
    serializer_class = UnitOfMeasureSerializer
    queryset = UnitOfMeasure.objects.all()
    permission_classes = [ReadOrCapability]
    write_capability = "reference.manage"

    filterset_fields = [
        "code",
    ]

    search_fields = [
        "code",
        "name",
        "symbol",
    ]

    ordering_fields = [
        "code",
        "name",
    ]

    ordering = [
        "name",
    ]


class ActorViewSet(AuthoredModelViewSet):
    serializer_class = ActorSerializer
    queryset = Actor.objects.all()
    permission_classes = [ReadOrCapability]
    write_capability = "reference.manage"

    filterset_fields = [
        "code",
        "level",
    ]

    search_fields = [
        "code",
        "name",
        "level",
        "phone",
        "email",
    ]

    ordering_fields = [
        "code",
        "name",
        "level",
    ]

    ordering = [
        "name",
    ]


class PartnerViewSet(AuthoredModelViewSet):
    serializer_class = PartnerSerializer
    queryset = Partner.objects.all()
    permission_classes = [ReadOrCapability]
    write_capability = "reference.manage"

    filterset_fields = [
        "code",
    ]

    search_fields = [
        "code",
        "name",
        "phone",
        "email",
    ]

    ordering_fields = [
        "code",
        "name",
    ]

    ordering = [
        "name",
    ]


class AuditLogViewSet(
    ProjectScopedQuerysetMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AuditLogSerializer

    queryset = AuditLog.objects.select_related(
        "project",
        "actor",
        "content_type",
    ).all()

    filterset_fields = [
        "action",
        "content_type",
        "actor",
    ]

    ordering = ["-at"]