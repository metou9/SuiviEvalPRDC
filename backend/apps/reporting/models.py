from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class ReportTemplate(BaseModel):
    class Code(models.TextChoices):
        QUARTERLY = "QUARTERLY", "Rapport trimestriel"
        ANNUAL = "ANNUAL", "Rapport annuel"
        CUSTOM = "CUSTOM", "Personnalisé"

    project = models.ForeignKey(
        "core.Project", on_delete=models.CASCADE, related_name="report_templates"
    )
    code = models.CharField(max_length=16, choices=Code.choices, default=Code.QUARTERLY)
    name = models.CharField(max_length=255)
    structure = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name


class Report(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        FINAL = "FINAL", "Final"

    project = models.ForeignKey("core.Project", on_delete=models.CASCADE, related_name="reports")
    template = models.ForeignKey(ReportTemplate, on_delete=models.PROTECT, related_name="reports")
    title = models.CharField(max_length=255)
    period_year = models.PositiveIntegerField()
    period_quarter = models.PositiveSmallIntegerField(null=True, blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.DRAFT)
    file = models.FileField(upload_to="reports/%Y/", null=True, blank=True)

    class Meta:
        ordering = ["-period_year", "-period_quarter"]

    def __str__(self):
        return self.title
