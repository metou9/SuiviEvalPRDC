import pytest
from rest_framework.test import APIClient


def _client(user, project):
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_PROJECT_ID=str(project.id))
    return client


@pytest.mark.django_db
def test_measurement_nested_create_and_filter(project, indicator, make_user, geo):
    from apps.indicators.models import Dimension, DimensionCategory, IndicatorDimension

    dim = Dimension.objects.create(project=project, code="SEX", name="Sexe")
    male = DimensionCategory.objects.create(dimension=dim, code="M", name="H")
    female = DimensionCategory.objects.create(dimension=dim, code="F", name="F")
    IndicatorDimension.objects.create(indicator=indicator, dimension=dim)

    field = make_user("field", "FIELD_AGENT")
    client = _client(field, project)
    resp = client.post(
        "/api/v1/measurements/",
        {
            "indicator": indicator.id,
            "geo_unit": geo["boghe"].id,
            "period_year": 2025,
            "period_quarter": 1,
            "value": "10",
            "measurement_values": [
                {"dimension_category": male.id, "value": "6"},
                {"dimension_category": female.id, "value": "4"},
            ],
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content
    mid = resp.json()["id"]
    # Filter by indicator works and the value is project-scoped.
    listing = client.get(f"/api/v1/measurements/?indicator={indicator.id}")
    assert listing.json()["count"] == 1
    # Transition action.
    sub = client.post(f"/api/v1/measurements/{mid}/submit/", {}, format="json")
    assert sub.status_code == 200
    assert sub.json()["record"]["status"] == "SUBMITTED"


@pytest.mark.django_db
def test_project_scoping_hides_other_projects(project, indicator, make_user):
    from apps.core.models import Project
    from apps.indicators.models import Indicator, IndicatorType, Measurement

    other = Project.objects.create(code="o", name="Other")
    it = IndicatorType.objects.create(project=other, code="PDO", name="x")
    oind = Indicator.objects.create(project=other, code="O1", name="o", indicator_type=it)
    Measurement.objects.create(project=other, indicator=oind, period_year=2025, value=5)
    Measurement.objects.create(project=project, indicator=indicator, period_year=2025, value=5)

    field = make_user("field", "FIELD_AGENT")
    client = _client(field, project)
    listing = client.get("/api/v1/measurements/")
    assert listing.json()["count"] == 1  # only this project's row


@pytest.mark.django_db
def test_field_agent_cannot_validate_via_api(project, indicator, make_user):
    from apps.indicators.models import Measurement

    field = make_user("field", "FIELD_AGENT")
    m = Measurement.objects.create(
        project=project, indicator=indicator, period_year=2025, value=5, status="SUBMITTED"
    )
    client = _client(field, project)
    resp = client.post(f"/api/v1/measurements/{m.id}/validate/", {}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_me_endpoint(project, make_user):
    field = make_user("field", "FIELD_AGENT")
    client = _client(field, project)
    resp = client.get("/api/v1/auth/me/")
    body = resp.json()
    assert body["current_project"] == project.id
    assert any(r["code"] == "FIELD_AGENT" for r in body["roles"])
    assert "measurement.create" in body["capabilities"]
