import pytest

from apps.accounts.capabilities import (
    accessible_geo_unit_ids,
    has_capability,
    user_capabilities,
)


@pytest.mark.django_db
def test_capability_matrix(project, make_user):
    field = make_user("field", "FIELD_AGENT")
    validator = make_user("val", "VALIDATOR")
    viewer = make_user("view", "VIEWER")

    assert "measurement.create" in user_capabilities(field, project)
    assert "measurement.validate" not in user_capabilities(field, project)
    assert "measurement.validate" in user_capabilities(validator, project)
    assert user_capabilities(viewer, project) == set()


@pytest.mark.django_db
def test_admin_has_everything(project, make_user):
    admin = make_user("a", "ADMIN")
    assert has_capability(admin, "measurement.consolidate", project=project)
    assert has_capability(admin, "users.manage", project=project)
    assert has_capability(admin, "anything.at.all", project=project)


@pytest.mark.django_db
def test_geo_scope_closure(project, make_user, geo):
    user = make_user("u", "ME_REGIONAL", scope_geo=geo["brakna"])
    allowed = accessible_geo_unit_ids(user, project)
    assert geo["brakna"].id in allowed
    assert geo["boghe"].id in allowed  # descendant included
    assert geo["rosso"].id not in allowed  # other wilaya excluded


@pytest.mark.django_db
def test_project_wide_user_has_no_geo_restriction(project, make_user):
    spec = make_user("s", "ME_SPECIALIST")
    assert accessible_geo_unit_ids(spec, project) is None
