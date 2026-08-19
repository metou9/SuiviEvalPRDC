from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import ProjectOwnedModel


class WorkPlan(ProjectOwnedModel):
    """
    Plan de Travail et Budget Annuel (PTBA).

    Exemple :
    - PTBA PRDC-VFS 2026
    - PTBA PRDC-VFS 2027
    """

    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="workplans",
    )

    code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
    )

    name = models.CharField(
        max_length=255,
    )

    year = models.PositiveIntegerField()

    version = models.CharField(
        max_length=50,
        blank=True,
    )

    start_date = models.DateField(
        null=True,
        blank=True,
    )

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    is_current = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = ["-year", "name"]

        constraints = [
            models.UniqueConstraint(
                fields=["project", "year", "version"],
                name="unique_workplan_project_year_version",
            ),
        ]

        indexes = [
            models.Index(fields=["project", "year"]),
            models.Index(fields=["is_current"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.year}"


class Activity(ProjectOwnedModel):
    """
    Activité de la programmation technique.

    Une activité appartient directement à une sous-composante.
    La composante est obtenue via :
        activity.program_node.parent

    Les champs created_at, updated_at, created_by et updated_by
    sont hérités automatiquement de ProjectOwnedModel.
    """

    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="activities",
    )

    # ------------------------------------------------------------------
    # Identification
    # ------------------------------------------------------------------

    code = models.CharField(
        max_length=50,
        null=True,
        blank=True,

    )

    title = models.CharField(
        max_length=500,
    )

    # ------------------------------------------------------------------
    # Exercice / PTBA
    # ------------------------------------------------------------------

    workplan = models.ForeignKey(
        "activities.WorkPlan",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activities",
    )

    # ------------------------------------------------------------------
    # Sous-composante
    # ------------------------------------------------------------------
    # L'activité est directement liée à une sous-composante.
    # La composante est obtenue par program_node.parent.
    # ------------------------------------------------------------------

    program_node = models.ForeignKey(
        "program.ProgramNode",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activities",
    )

    # ------------------------------------------------------------------
    # Responsable / Partenaire
    # ------------------------------------------------------------------

    responsible = models.ForeignKey(
        "core.Partner",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activities",
    )

    # ------------------------------------------------------------------
    # Programmation temporelle
    # ------------------------------------------------------------------

    start_date = models.DateField(
        null=True,
        blank=True,
    )

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    # ------------------------------------------------------------------
    # Unité et quantité programmée
    # ------------------------------------------------------------------

    unit = models.ForeignKey(
        "core.UnitOfMeasure",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activities",
    )

    planned_quantity = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # ------------------------------------------------------------------
    # Importance
    # ------------------------------------------------------------------

    importance = models.CharField(
        max_length=255,
        blank=True,
    )

    # ------------------------------------------------------------------
    # Budget programmé
    # ------------------------------------------------------------------

    programmed_budget = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # ------------------------------------------------------------------
    # Description
    # Conservée pour utilisation éventuelle.
    # ------------------------------------------------------------------

    description = models.TextField(
        null=True,
        blank=True,
        default=None,
    )

    # Historisation existante du module Activity
    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "code"],
                name="unique_activity_code_per_project",
            ),
        ]

        indexes = [
            models.Index(fields=["project", "code"]),
            models.Index(fields=["workplan"]),
            models.Index(fields=["program_node"]),
            models.Index(fields=["responsible"]),
        ]

        ordering = ["code"]

    def clean(self):
        super().clean()

        from django.core.exceptions import ValidationError
        from apps.program.models import ProgramNode

        # --------------------------------------------------------------
        # Sous-composante obligatoire si renseignée
        # --------------------------------------------------------------

        if self.program_node_id:
            if (
                self.program_node.node_type
                != ProgramNode.NodeType.SUBCOMPONENT
            ):
                raise ValidationError({
                    "program_node":
                    "Une activité doit être rattachée à une sous-composante."
                })

            if self.program_node.project_id != self.project_id:
                raise ValidationError({
                    "program_node":
                    "La sous-composante doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # PTBA du même projet
        # --------------------------------------------------------------

        if self.workplan_id:
            if self.workplan.project_id != self.project_id:
                raise ValidationError({
                    "workplan":
                    "L'exercice/PTBA doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # Responsable / Partenaire du même projet
        # --------------------------------------------------------------

        if self.responsible_id:
            if self.responsible.project_id != self.project_id:
                raise ValidationError({
                    "responsible":
                    "Le responsable/partenaire doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # Unité de mesure du même projet
        # --------------------------------------------------------------

        if self.unit_id:
            if self.unit.project_id != self.project_id:
                raise ValidationError({
                    "unit":
                    "L'unité de mesure doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # Cohérence des dates
        # --------------------------------------------------------------

        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError({
                    "end_date":
                    "La date de fin ne peut pas être antérieure à la date de début."
                })

    def __str__(self):
        return f"{self.code} — {self.title}"


class ActivityParticipant(models.Model):
    class Sex(models.TextChoices):
        M = "M", "Homme"
        F = "F", "Femme"

    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="participants",
    )

    full_name = models.CharField(
        max_length=255,
    )

    origin = models.CharField(
        max_length=255,
        blank=True,
    )

    organization = models.CharField(
        max_length=255,
        blank=True,
    )

    function = models.CharField(
        max_length=255,
        blank=True,
    )

    sex = models.CharField(
        max_length=1,
        choices=Sex.choices,
        blank=True,
    )