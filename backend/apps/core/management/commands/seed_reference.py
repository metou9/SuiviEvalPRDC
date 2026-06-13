"""Generic reference-data skeleton seed for a brand-new project.

Creates an empty, configurable project with the standard indicator types, the two
common dimensions and the standard procurement stages — but NO project-specific
geography/programme/indicators (those are configured via the admin screens). Use
``seed_prdc`` for the populated PRDC-VFS reference project.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Role
from apps.core.models import Project
from apps.indicators.models import Dimension, DimensionCategory, IndicatorType
from apps.procurement.models import ProcurementStage
from apps.reporting.models import ReportTemplate

from .seed_prdc import INDICATOR_TYPES, PROCUREMENT_STAGES, ROLES


class Command(BaseCommand):
    help = "Seed a generic, empty project skeleton (reference data only)."

    def add_arguments(self, parser):
        parser.add_argument("--code", required=True)
        parser.add_argument("--name", required=True)
        parser.add_argument("--currency-code", default="USD")
        parser.add_argument("--currency-symbol", default="$")

    @transaction.atomic
    def handle(self, *args, **options):
        for code, name in ROLES:
            Role.objects.update_or_create(
                code=code, defaults={"name": name, "is_system": True}
            )
        project, _ = Project.objects.update_or_create(
            code=options["code"],
            defaults={
                "name": options["name"],
                "currency_code": options["currency_code"],
                "currency_symbol": options["currency_symbol"],
            },
        )
        for code, name, order in INDICATOR_TYPES:
            IndicatorType.objects.update_or_create(
                project=project, code=code, defaults={"name": name, "order": order}
            )
        sex, _ = Dimension.objects.update_or_create(
            project=project, code="SEX", defaults={"name": "Sex", "order": 0}
        )
        for code, name, order in [("M", "Male", 0), ("F", "Female", 1)]:
            DimensionCategory.objects.update_or_create(
                dimension=sex, code=code, defaults={"name": name, "order": order}
            )
        for code, name, order in PROCUREMENT_STAGES:
            ProcurementStage.objects.update_or_create(
                project=project, code=code, defaults={"name": name, "order": order}
            )
        ReportTemplate.objects.update_or_create(
            project=project, code="QUARTERLY",
            defaults={"name": "Quarterly report", "structure": {"sections": []}},
        )
        self.stdout.write(self.style.SUCCESS(f"Seeded skeleton project '{project.code}'."))
