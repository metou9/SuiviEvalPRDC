"""Centralised capability registry + ``has_capability`` (capability AND scope).

A capability code is ``"<area>.<step>"`` (e.g. ``measurement.validate``) or a flat
code (``config.manage``, ``users.manage``, ``report.generate``). The workflow areas
share the same five steps so the matrix in 03_rbac_and_workflow.md stays compact.
"""
from functools import lru_cache

EXEC_AREAS = ["measurement", "activity"]
WORKFLOW_STEPS = ["create", "submit", "validate", "audit", "consolidate"]


def _caps(areas, steps):
    return {f"{a}.{s}" for a in areas for s in steps}


# Role code -> set of capability codes. ADMIN is handled specially (all).
ROLE_CAPABILITIES = {
    "ADMIN": {"*"},
    "COORDINATOR": (
        _caps(["financialtransaction", "procurementprocess"], ["validate", "audit", "consolidate"])
        | {"report.generate"}
    ),
    "ME_SPECIALIST": (
        _caps(EXEC_AREAS, WORKFLOW_STEPS)
        | _caps(["financialtransaction"], ["validate", "audit", "consolidate"])
        | {"report.generate", "config.manage"}
    ),
    "ME_REGIONAL": (
        _caps(EXEC_AREAS, ["create", "submit", "validate"]) | {"grievance.create", "grievance.submit"}
    ),
    "FIELD_AGENT": (
        _caps(EXEC_AREAS, ["create", "submit"]) | {"grievance.create", "grievance.submit"}
    ),
    "VALIDATOR": _caps(EXEC_AREAS, ["validate"]),
    "AUDITOR": _caps(EXEC_AREAS, ["audit"]),
    "RAF": (
        _caps(["financialtransaction"], WORKFLOW_STEPS)
        | _caps(["procurementprocess"], ["validate", "audit", "consolidate"])
        | {"report.generate"}
    ),
    "PROCUREMENT_OFFICER": _caps(["procurementprocess"], WORKFLOW_STEPS),
    "GENDER_OFFICER": set(),
    "INFRA_ENGINEER": set(),
    "GRIEVANCE_OFFICER": (
        _caps(["grievance"], WORKFLOW_STEPS) | {"grievance.resolve"}
    ),
    "LOCAL_DEV_OFFICER": set(),
    "COMPONENT_MANAGER": _caps(EXEC_AREAS, ["create", "submit"]),
    "EXTERNAL_CONSULTANT": set(),
    "VALIDATION_COMMITTEE": set(),
    "VIEWER": set(),
}

# Steps that a named IndicatorResponsibility may unlock for a specialised reviewer.
_RESPONSIBILITY_STEP = {
    "validate": "VALIDATION",
    "audit": "AUDIT",
    "consolidate": "TRANSFER_MIS",
}


def _user_role_assignments(user, project):
    if not user or not getattr(user, "is_authenticated", False):
        return []
    return list(
        user.role_assignments.filter(project=project, is_active=True).select_related(
            "role", "scope_geo", "scope_program"
        )
    )


def user_capabilities(user, project):
    """Union of capability codes granted to the user in the project."""
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    if user.is_superuser:
        return {"*"}
    caps = set()
    for ra in _user_role_assignments(user, project):
        grants = ROLE_CAPABILITIES.get(ra.role.code, set())
        if grants == {"*"}:
            return {"*"}
        caps |= grants
    return caps


def accessible_geo_unit_ids(user, project):
    """Set of geo-unit ids the user may touch, or ``None`` for whole-project access."""
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    if user.is_superuser:
        return None
    assignments = _user_role_assignments(user, project)
    if not assignments:
        return set()
    scopes = [ra.scope_geo for ra in assignments]
    if any(s is None for s in scopes):
        return None  # at least one role is project-wide
    from apps.geo.models import GeoUnit

    ids = set()
    for unit in scopes:
        ids |= GeoUnit.descendants_ids(unit)
    return ids


def _in_geo_scope(user, project, obj):
    allowed = accessible_geo_unit_ids(user, project)
    if allowed is None:
        return True
    geo = getattr(obj, "geo_unit", None) or getattr(obj, "scope_geo", None)
    if geo is None:
        return True  # project-wide record
    return geo.id in allowed


def _responsibility_override(user, project, capability, obj):
    """A specialised reviewer named in IndicatorResponsibility may act on that indicator."""
    if "." not in capability:
        return False
    area, step = capability.split(".", 1)
    if area != "measurement" or step not in _RESPONSIBILITY_STEP:
        return False
    indicator = getattr(obj, "indicator", None)
    if indicator is None:
        return False
    resp_kind = _RESPONSIBILITY_STEP[step]
    role_codes = {ra.role.code for ra in _user_role_assignments(user, project)}
    from apps.indicators.models import IndicatorResponsibility

    qs = IndicatorResponsibility.objects.filter(indicator=indicator, responsibility=resp_kind)
    for resp in qs.select_related("role", "user"):
        if resp.user_id == user.id:
            return True
        if resp.role and resp.role.code in role_codes:
            return True
    return False


def has_capability(user, capability, obj=None, project=None):
    """True if the user holds the capability AND the object is in scope."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    if project is None:
        project = getattr(obj, "project", None)
    caps = user_capabilities(user, project)
    granted = "*" in caps or capability in caps
    if not granted:
        granted = _responsibility_override(user, project, capability, obj)
    if not granted:
        return False
    if obj is not None:
        return _in_geo_scope(user, project, obj)
    return True
