import pytest


@pytest.fixture
def project(db):
    from apps.core.models import Milestone, Project

    p = Project.objects.create(code="t", name="Test", currency_code="MRU", currency_symbol="UM")
    Milestone.objects.create(project=p, code="CLOSING", name="Clôture", order=2)
    return p


@pytest.fixture
def roles(db):
    from apps.accounts.models import Role

    out = {}
    for code in [
        "ADMIN", "ME_SPECIALIST", "FIELD_AGENT", "VALIDATOR", "AUDITOR",
        "VIEWER", "ME_REGIONAL", "RAF",
    ]:
        out[code] = Role.objects.create(code=code, name=code, is_system=True)
    return out


@pytest.fixture
def make_user(db, project, roles):
    from apps.accounts.models import ProjectMembership, RoleAssignment, User

    def _make(username, role_code, scope_geo=None):
        user = User.objects.create_user(username=username, password="pw12345")
        ProjectMembership.objects.create(project=project, user=user, is_default=True)
        RoleAssignment.objects.create(
            user=user, role=roles[role_code], project=project, scope_geo=scope_geo
        )
        return user

    return _make


@pytest.fixture
def geo(db, project):
    from apps.geo.models import GeoLevel, GeoUnit

    wil_level = GeoLevel.objects.create(project=project, name="Wilaya", rank=0, code="WIL")
    com_level = GeoLevel.objects.create(project=project, name="Commune", rank=1, code="COM")
    brakna = GeoUnit.objects.create(project=project, geo_level=wil_level, name="Brakna", code="W-BR")
    trarza = GeoUnit.objects.create(project=project, geo_level=wil_level, name="Trarza", code="W-TR")
    boghe = GeoUnit.objects.create(
        project=project, geo_level=com_level, parent=brakna, name="Boghé", code="C-BO"
    )
    rosso = GeoUnit.objects.create(
        project=project, geo_level=com_level, parent=trarza, name="Rosso", code="C-RO"
    )
    return {"brakna": brakna, "trarza": trarza, "boghe": boghe, "rosso": rosso}


@pytest.fixture
def indicator(db, project):
    from apps.indicators.models import Indicator, IndicatorType

    it = IndicatorType.objects.create(project=project, code="INTERMEDIATE", name="Int")
    return Indicator.objects.create(
        project=project, code="I1", name="Ind 1", indicator_type=it, unit="NUMBER",
        aggregation_method="SUM",
    )
