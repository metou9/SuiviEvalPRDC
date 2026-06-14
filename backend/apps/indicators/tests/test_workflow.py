import pytest

from apps.core.models import StateEvent, WorkflowError
from apps.indicators.models import Measurement


def _measurement(project, indicator, geo_unit=None):
    return Measurement.objects.create(
        project=project, indicator=indicator, geo_unit=geo_unit,
        period_year=2025, period_quarter=1, value=10,
    )


@pytest.mark.django_db
def test_full_lifecycle_with_authorised_users(project, indicator, make_user):
    field = make_user("field", "FIELD_AGENT")
    validator = make_user("val", "VALIDATOR")
    auditor = make_user("aud", "AUDITOR")
    specialist = make_user("spec", "ME_SPECIALIST")
    m = _measurement(project, indicator)

    m.transition(field, "submit")
    assert m.status == "SUBMITTED"
    m.transition(validator, "validate")
    assert m.status == "VALIDATED"
    m.transition(auditor, "audit")
    assert m.status == "AUDITED"
    m.transition(specialist, "consolidate")
    assert m.status == "CONSOLIDATED"
    # Each transition wrote a StateEvent.
    assert StateEvent.objects.filter(object_id=m.id).count() == 4


@pytest.mark.django_db
def test_validate_requires_capability(project, indicator, make_user):
    field = make_user("field", "FIELD_AGENT")
    m = _measurement(project, indicator)
    m.transition(field, "submit")
    # A field agent cannot validate.
    with pytest.raises(WorkflowError):
        m.transition(field, "validate")


@pytest.mark.django_db
def test_illegal_transition_raises(project, indicator, make_user):
    spec = make_user("spec", "ME_SPECIALIST")
    m = _measurement(project, indicator)
    # Cannot consolidate straight from DRAFT.
    with pytest.raises(WorkflowError):
        m.transition(spec, "consolidate")


@pytest.mark.django_db
def test_geo_scope_blocks_out_of_scope_transition(project, indicator, make_user, geo):
    # Validator scoped to Brakna cannot validate a Trarza/Rosso measurement.
    validator = make_user("val", "VALIDATOR", scope_geo=geo["brakna"])
    field = make_user("field", "FIELD_AGENT")
    m = _measurement(project, indicator, geo_unit=geo["rosso"])
    m.transition(field, "submit")
    with pytest.raises(WorkflowError):
        m.transition(validator, "validate")
    # But it can validate a Boghé (Brakna child) measurement.
    m2 = _measurement(project, indicator, geo_unit=geo["boghe"])
    m2.transition(field, "submit")
    event = m2.transition(validator, "validate")
    assert event.to_state == "VALIDATED"
