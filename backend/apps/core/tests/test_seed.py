import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_seed_prdc_idempotent_and_counts():
    from apps.finance.models import ExpenseCategory
    from apps.geo.models import GeoUnit
    from apps.indicators.models import Indicator
    from apps.procurement.models import ProcurementMethod, ProcurementStage
    from apps.program.models import ProgramNode

    call_command("seed_prdc")
    call_command("seed_prdc")  # second run must not duplicate

    assert GeoUnit.objects.filter(geo_level__rank=2).count() == 17
    assert ProgramNode.objects.filter(parent__isnull=True).count() == 4
    assert ProgramNode.objects.filter(parent__isnull=False).count() == 7
    assert Indicator.objects.count() >= 20
    assert ExpenseCategory.objects.count() == 6
    assert ProcurementMethod.objects.count() == 6
    assert ProcurementStage.objects.count() == 5
