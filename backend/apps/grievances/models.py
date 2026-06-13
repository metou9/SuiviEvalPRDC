from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import BaseModel, ProjectOwnedModel, WorkflowMixin


class GrievanceType(BaseModel):
    project = models.ForeignKey(
        "core.Project", on_delete=models.CASCADE, related_name="grievance_types"
    )
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=255)
    sla_days = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("project", "code")]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Grievance(WorkflowMixin, ProjectOwnedModel):
    WORKFLOW_AREA = "grievance"

    class Level(models.TextChoices):
        LOCAL = "LOCAL", "Local"
        REGIONAL = "REGIONAL", "Régional"
        NATIONAL = "NATIONAL", "National"
        OTHER = "OTHER", "Autre"

    class State(models.TextChoices):
        RECEIVED = "RECEIVED", "Reçue"
        IN_PROGRESS = "IN_PROGRESS", "En cours"
        RESOLVED = "RESOLVED", "Résolue"
        CLOSED = "CLOSED", "Clôturée"
        REJECTED = "REJECTED", "Rejetée"

    project = models.ForeignKey("core.Project", on_delete=models.CASCADE, related_name="grievances")
    grievance_type = models.ForeignKey(
        GrievanceType, on_delete=models.PROTECT, related_name="grievances"
    )
    geo_unit = models.ForeignKey(
        "geo.GeoUnit", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    level = models.CharField(max_length=16, choices=Level.choices, default=Level.LOCAL)
    channel = models.CharField(max_length=120, blank=True)
    summary = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    complainant_name = models.CharField(max_length=255, blank=True)
    is_anonymous = models.BooleanField(default=False)
    received_at = models.DateField()
    resolved_at = models.DateField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    state = models.CharField(max_length=16, choices=State.choices, default=State.RECEIVED)
    history = HistoricalRecords()

    class Meta:
        indexes = [models.Index(fields=["project", "state"]), models.Index(fields=["status"])]
        ordering = ["-received_at"]

    @property
    def effective_sla_days(self):
        return self.grievance_type.sla_days or self.project.grievance_sla_days

    @property
    def is_within_sla(self):
        if self.resolved_at is None:
            return None
        return (self.resolved_at - self.received_at).days <= self.effective_sla_days

    def __str__(self):
        return self.summary
