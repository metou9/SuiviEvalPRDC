from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import BaseModel, ProjectOwnedModel, WorkflowMixin


class IndicatorType(BaseModel):
    class Code(models.TextChoices):
        PDO = "PDO", "Indicateurs de l'ODP"
        OUTCOME = "OUTCOME", "Résultats"
        INTERMEDIATE = "INTERMEDIATE", "Indicateurs intermédiaires"
        OUTPUT = "OUTPUT", "Produits"
        EXECUTION = "EXECUTION", "Indicateurs d'exécution"
        IMPACT = "IMPACT", "Indicateurs d'impact"

    project = models.ForeignKey(
        "core.Project", on_delete=models.CASCADE, related_name="indicator_types"
    )
    code = models.CharField(max_length=16)
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("project", "code")]
        ordering = ["order"]

    def __str__(self):
        return self.code


class Dimension(BaseModel):
    project = models.ForeignKey("core.Project", on_delete=models.CASCADE, related_name="dimensions")
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("project", "code")]
        ordering = ["order"]

    def __str__(self):
        return self.code


class DimensionCategory(BaseModel):
    dimension = models.ForeignKey(Dimension, on_delete=models.CASCADE, related_name="categories")
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("dimension", "code")]
        ordering = ["order"]

    def __str__(self):
        return f"{self.dimension.code}:{self.code}"


class Indicator(BaseModel):
    class Unit(models.TextChoices):
        NUMBER = "NUMBER", "Nombre"
        PERCENTAGE = "PERCENTAGE", "Pourcentage"
        CURRENCY = "CURRENCY", "Monétaire"
        RATIO = "RATIO", "Ratio"
        TEXT = "TEXT", "Texte"

    class Direction(models.TextChoices):
        INCREASE = "INCREASE", "Croissant"
        DECREASE = "DECREASE", "Décroissant"

    class Aggregation(models.TextChoices):
        SUM = "SUM", "Somme"
        AVERAGE = "AVERAGE", "Moyenne"
        LAST = "LAST", "Dernière valeur"
        MAX = "MAX", "Maximum"
        MIN = "MIN", "Minimum"
        MANUAL = "MANUAL", "Manuel"

    class Frequency(models.TextChoices):
        MONTHLY = "MONTHLY", "Mensuel"
        QUARTERLY = "QUARTERLY", "Trimestriel"
        SEMESTERLY = "SEMESTERLY", "Semestriel"
        ANNUAL = "ANNUAL", "Annuel"
        ADHOC = "ADHOC", "Ponctuel"

    project = models.ForeignKey("core.Project", on_delete=models.CASCADE, related_name="indicators")
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=500)
    definition = models.TextField(blank=True)
    indicator_type = models.ForeignKey(
        IndicatorType, on_delete=models.PROTECT, related_name="indicators"
    )
    program_node = models.ForeignKey(
        "program.ProgramNode", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="indicators",
    )
    unit = models.CharField(max_length=16, choices=Unit.choices, default=Unit.NUMBER)
    direction = models.CharField(max_length=16, choices=Direction.choices, default=Direction.INCREASE)
    aggregation_method = models.CharField(
        max_length=16, choices=Aggregation.choices, default=Aggregation.SUM
    )
    is_cri = models.BooleanField(default=False)
    reporting_frequency = models.CharField(
        max_length=16, choices=Frequency.choices, default=Frequency.QUARTERLY
    )
    data_source = models.CharField(max_length=500, blank=True)
    collection_tool = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    dimensions = models.ManyToManyField(
        Dimension, through="IndicatorDimension", related_name="indicators", blank=True
    )
    history = HistoricalRecords()

    class Meta:
        unique_together = [("project", "code")]
        ordering = ["order", "code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class IndicatorResponsibility(BaseModel):
    class Kind(models.TextChoices):
        COLLECTION = "COLLECTION", "Collecte"
        VALIDATION = "VALIDATION", "Validation"
        AUDIT = "AUDIT", "Audit/Contrôle"
        TRANSFER_MIS = "TRANSFER_MIS", "Transfert vers le MIS"
        AGGREGATION = "AGGREGATION", "Agrégation"
        ANALYSIS = "ANALYSIS", "Analyse"

    indicator = models.ForeignKey(
        Indicator, on_delete=models.CASCADE, related_name="responsibilities"
    )
    responsibility = models.CharField(max_length=16, choices=Kind.choices)
    role = models.ForeignKey(
        "accounts.Role", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    user = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    note = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return f"{self.indicator.code}:{self.responsibility}"


class IndicatorDimension(models.Model):
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE)
    dimension = models.ForeignKey(Dimension, on_delete=models.CASCADE)

    class Meta:
        unique_together = [("indicator", "dimension")]


class IndicatorTarget(BaseModel):
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE, related_name="targets")
    milestone = models.ForeignKey("core.Milestone", on_delete=models.CASCADE, related_name="targets")
    geo_unit = models.ForeignKey(
        "geo.GeoUnit", null=True, blank=True, on_delete=models.CASCADE, related_name="+"
    )
    value = models.DecimalField(max_digits=18, decimal_places=2)
    note = models.CharField(max_length=500, blank=True)

    class Meta:
        unique_together = [("indicator", "milestone", "geo_unit")]

    def __str__(self):
        return f"{self.indicator.code}@{self.milestone.code}={self.value}"


class Measurement(WorkflowMixin, ProjectOwnedModel):
    WORKFLOW_AREA = "measurement"

    class Source(models.TextChoices):
        MANUAL = "MANUAL", "Saisie manuelle"
        IMPORT = "IMPORT", "Import"
        SURVEY = "SURVEY", "Enquête"

    project = models.ForeignKey(
        "core.Project", on_delete=models.CASCADE, related_name="measurements"
    )
    indicator = models.ForeignKey(Indicator, on_delete=models.PROTECT, related_name="measurements")
    geo_unit = models.ForeignKey(
        "geo.GeoUnit", null=True, blank=True, on_delete=models.SET_NULL, related_name="measurements"
    )
    program_node = models.ForeignKey(
        "program.ProgramNode", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    period_year = models.PositiveIntegerField()
    period_quarter = models.PositiveSmallIntegerField(null=True, blank=True)
    period_month = models.PositiveSmallIntegerField(null=True, blank=True)
    period_date = models.DateField(null=True, blank=True)
    value = models.DecimalField(max_digits=18, decimal_places=2)
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.MANUAL)
    narrative = models.TextField(blank=True)
    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=["indicator", "period_year", "period_quarter"]),
            models.Index(fields=["geo_unit"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.indicator.code} {self.period_year} = {self.value}"


class MeasurementValue(models.Model):
    measurement = models.ForeignKey(
        Measurement, on_delete=models.CASCADE, related_name="measurement_values"
    )
    dimension_category = models.ForeignKey(
        DimensionCategory, on_delete=models.CASCADE, related_name="+"
    )
    value = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        unique_together = [("measurement", "dimension_category")]
