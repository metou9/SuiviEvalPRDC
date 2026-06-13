"""Resolve the current project from the ``X-Project-Id`` header (membership-checked).

JWT authentication happens inside DRF (not Django's session middleware), so
``request.user`` is anonymous at middleware time. We therefore expose
``request.project`` as a lazy object that authenticates on first access.
"""
from django.utils.functional import SimpleLazyObject

from apps.core.models import Project


def _request_user(request):
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return user
    try:
        from rest_framework_simplejwt.authentication import JWTAuthentication

        result = JWTAuthentication().authenticate(request)
    except Exception:
        result = None
    return result[0] if result else None


def _resolve_project(request):
    user = _request_user(request)
    if user is None or not user.is_authenticated:
        return None
    header = request.headers.get("X-Project-Id")
    if header:
        try:
            pid = int(header)
        except (TypeError, ValueError):
            return None
        if user.is_superuser:
            return Project.objects.filter(pk=pid).first()
        membership = user.memberships.filter(project_id=pid).select_related("project").first()
        return membership.project if membership else None
    membership = (
        user.memberships.order_by("-is_default", "joined_at").select_related("project").first()
    )
    if membership:
        return membership.project
    if user.is_superuser:
        return Project.objects.first()
    return None


class CurrentProjectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.project = SimpleLazyObject(lambda: _resolve_project(request))
        return self.get_response(request)
