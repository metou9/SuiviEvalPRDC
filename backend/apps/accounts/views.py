import time

import jwt
from django.conf import settings
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.core.api import ProjectScopedQuerysetMixin

from .capabilities import user_capabilities
from .models import Role, RoleAssignment
from .permissions import ReadOrCapability
from .serializers import (
    MembershipSerializer,
    RoleAssignmentSerializer,
    RoleSerializer,
    UserSerializer,
)
from django.contrib.auth import get_user_model

User = get_user_model()


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        user = request.user
        project = getattr(request, "project", None)
        memberships = MembershipSerializer(
            user.memberships.select_related("project").all(), many=True
        ).data
        roles = []
        if project:
            for ra in user.role_assignments.filter(
                project=project, is_active=True
            ).select_related("role"):
                roles.append(
                    {
                        "code": ra.role.code,
                        "scope_geo": ra.scope_geo_id,
                        "scope_program": ra.scope_program_id,
                    }
                )
        caps = sorted(user_capabilities(user, project)) if project else []
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name or user.get_full_name() or user.username,
                "default_locale": user.default_locale or "fr",
                "current_project": project.id if project else None,
                "projects": memberships,
                "roles": roles,
                "capabilities": caps,
                "is_superuser": user.is_superuser,
            }
        )


class UserViewSet(ModelViewSet):
    """ADMIN-only user administration."""
    queryset = User.objects.all().order_by("username")
    serializer_class = UserSerializer
    permission_classes = [ReadOrCapability]
    write_capability = "users.manage"
    search_fields = ["username", "email", "display_name", "first_name", "last_name"]
    ordering_fields = ["username", "id"]


class RoleViewSet(ModelViewSet):
    queryset = Role.objects.all().order_by("code")
    serializer_class = RoleSerializer
    permission_classes = [ReadOrCapability]
    write_capability = "users.manage"
    search_fields = ["code", "name"]


class RoleAssignmentViewSet(ProjectScopedQuerysetMixin, ModelViewSet):
    queryset = RoleAssignment.objects.all().select_related("role", "user")
    serializer_class = RoleAssignmentSerializer
    permission_classes = [ReadOrCapability]
    write_capability = "users.manage"
    filterset_fields = ["user", "role", "is_active"]

    def perform_create(self, serializer):
        serializer.save(project=self.request.project)


class MetabaseEmbedView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        try:
            dashboard_id = int(request.query_params["dashboard"])
        except (KeyError, ValueError):
            return Response({"detail": "dashboard query param required"}, status=400)
        project = getattr(request, "project", None)
        if not project:
            return Response({"detail": "no project selected"}, status=400)
        params = {"project_id": project.id}
        for key in ("fiscal_year", "indicator_type", "program_node", "status"):
            if key in request.query_params:
                params[key] = request.query_params[key]
        payload = {
            "resource": {"dashboard": dashboard_id},
            "params": params,
            "exp": round(time.time()) + 10 * 60,
        }
        token = jwt.encode(payload, settings.METABASE_EMBEDDING_SECRET, algorithm="HS256")
        url = (
            f"{settings.METABASE_SITE_URL}/embed/dashboard/{token}"
            f"#bordered=false&titled=false&theme=light"
        )
        return Response({"iframe_url": url})
