"""Thin permission classes that delegate to ``accounts.capabilities``."""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .capabilities import has_capability


class ReadOrCapability(BasePermission):
    """Read for any authenticated user in the project; write requires a capability.

    The view declares ``write_capability`` (e.g. ``"config.manage"``).
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        cap = getattr(view, "write_capability", None)
        if cap is None:
            return True
        return has_capability(request.user, cap, project=getattr(request, "project", None))


class WorkflowObjectPermission(BasePermission):
    """Create/edit-draft is gated by ``<area>.create``; transitions self-check."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in ("POST",) and view.action == "create":
            area = getattr(view, "workflow_area", None)
            if area:
                return has_capability(
                    request.user, f"{area}.create", project=getattr(request, "project", None)
                )
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.method in ("PUT", "PATCH", "DELETE"):
            area = getattr(view, "workflow_area", None)
            if area:
                return has_capability(request.user, f"{area}.create", obj=obj)
        return True
