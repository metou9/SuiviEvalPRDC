from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import BaseModel, ProjectOwnedModel, WorkflowMixin


class Activity(WorkflowMixin, ProjectOwnedModel):
    WORKFLOW_AREA = "activity"

    class Kind(models.TextChoices):
        TRAINING = "TRAINING", "Formation"
        AWARENESS = "AWARENESS", "Sensibilisation"
        FIELD_VISIT = "FIELD_VISIT", "Visite de terrain"
        VISIT_RECEIVED = "VISIT_RECEIVED", "Visite reçue"
        MEETING = "MEETING", "Réunion"
        SUBPROJECT = "SUBPROJECT", "Sous-projet"
        STAKEHOLDER = "STAKEHOLDER", "Autre intervenant"
        OBSERVATION = "OBSERVATION", "Changement observé"

    project = models.ForeignKey("core.Project", on_delete=models.CASCADE, related_name="activities")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    geo_unit = models.ForeignKey(
        "geo.GeoUnit", null=True, blank=True, on_delete=models.SET_NULL, related_name="activities"
    )
    program_node = models.ForeignKey(
        "program.ProgramNode", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    indicator = models.ForeignKey(
        "indicators.Indicator", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    title = models.CharField(max_length=500)
    date = models.DateField()
    location = models.CharField(max_length=255, blank=True)
    organizer = models.CharField(max_length=255, blank=True)
    duration_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    objective = models.TextField(blank=True)
    description = models.TextField(blank=True)
    total_participants = models.PositiveIntegerField(null=True, blank=True)
    women_count = models.PositiveIntegerField(null=True, blank=True)
    youth_count = models.PositiveIntegerField(null=True, blank=True)

    # Sub-project fields
    submission_date = models.DateField(null=True, blank=True)
    funding_requested = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    funding_obtained = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    funding_date = models.DateField(null=True, blank=True)
    management_committee = models.CharField(max_length=500, blank=True)
    beneficiary_org = models.CharField(max_length=500, blank=True)

    # Stakeholder fields
    actor_name = models.CharField(max_length=255, blank=True)
    implantation_date = models.DateField(null=True, blank=True)
    main_actions = models.TextField(blank=True)

    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=["project", "kind", "date"]),
            models.Index(fields=["geo_unit"]),
            models.Index(fields=["status"]),
        ]
        ordering = ["-date"]

    def __str__(self):
        return f"[{self.kind}] {self.title}"


class ActivityParticipant(models.Model):
    class Sex(models.TextChoices):
        M = "M", "Homme"
        F = "F", "Femme"

    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="participants")
    full_name = models.CharField(max_length=255)
    origin = models.CharField(max_length=255, blank=True)
    organization = models.CharField(max_length=255, blank=True)
    function = models.CharField(max_length=255, blank=True)
    sex = models.CharField(max_length=1, choices=Sex.choices, blank=True)
