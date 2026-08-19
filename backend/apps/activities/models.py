from django.core.exceptions import ValidationError
from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import ProjectOwnedModel


# ======================================================================
# PTBA / PLAN DE TRAVAIL ANNUEL
# ======================================================================

class WorkPlan(ProjectOwnedModel):
    """
    Plan de Travail et Budget Annuel (PTBA).

    Exemples :
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


# ======================================================================
# ACTIVITÉ
# ======================================================================

class Activity(ProjectOwnedModel):
    """
    Activité de référence du projet.

    Une activité appartient directement à une sous-composante.

    La composante est obtenue via :

        activity.program_node.parent

    Les données propres à une année/PTBA ne sont pas stockées ici.
    Elles sont enregistrées dans TechnicalPlan.
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
    # Sous-composante
    # ------------------------------------------------------------------

    program_node = models.ForeignKey(
        "program.ProgramNode",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activities",
    )

    # ------------------------------------------------------------------
    # Zone d'intervention
    #
    # Peut représenter :
    # - Wilaya
    # - Moughataa
    # - Commune
    # - Village
    # ------------------------------------------------------------------

    geo_unit = models.ForeignKey(
        "geo.GeoUnit",
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
    # Unité de mesure
    # ------------------------------------------------------------------

    unit = models.ForeignKey(
        "core.UnitOfMeasure",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activities",
    )

    # ------------------------------------------------------------------
    # Indicateur lié
    # ------------------------------------------------------------------

    indicator = models.ForeignKey(
        "indicators.Indicator",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activities",
    )

    # ------------------------------------------------------------------
    # Informations générales
    # ------------------------------------------------------------------

    objective = models.TextField(
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    # ------------------------------------------------------------------
    # Historisation
    # ------------------------------------------------------------------

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
            models.Index(fields=["program_node"]),
            models.Index(fields=["geo_unit"]),
            models.Index(fields=["responsible"]),
            models.Index(fields=["indicator"]),
        ]

        ordering = ["code"]

    def clean(self):
        super().clean()

        from apps.program.models import ProgramNode

        # --------------------------------------------------------------
        # Sous-composante
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
        # Zone géographique
        # --------------------------------------------------------------

        if self.geo_unit_id:
            if self.geo_unit.project_id != self.project_id:
                raise ValidationError({
                    "geo_unit":
                    "La zone d'intervention doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # Responsable
        # --------------------------------------------------------------

        if self.responsible_id:
            if self.responsible.project_id != self.project_id:
                raise ValidationError({
                    "responsible":
                    "Le responsable/partenaire doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # Unité
        # --------------------------------------------------------------

        if self.unit_id:
            if self.unit.project_id != self.project_id:
                raise ValidationError({
                    "unit":
                    "L'unité de mesure doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # Indicateur
        # --------------------------------------------------------------

        if self.indicator_id:
            if self.indicator.project_id != self.project_id:
                raise ValidationError({
                    "indicator":
                    "L'indicateur doit appartenir au même projet."
                })

    def __str__(self):
        if self.code:
            return f"{self.code} — {self.title}"

        return self.title


# ======================================================================
# PROGRAMMATION TECHNIQUE PTBA
# ======================================================================

class TechnicalPlan(ProjectOwnedModel):
    """
    Programmation annuelle d'une activité dans un PTBA.

    Une Activity représente l'activité de référence.

    TechnicalPlan représente sa programmation pour un PTBA donné :
    quantité prévue, dates, modalités de mise en œuvre,
    extrant attendu, observations, etc.
    """

    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="technical_plans",
    )

    # ------------------------------------------------------------------
    # PTBA
    # ------------------------------------------------------------------

    workplan = models.ForeignKey(
        WorkPlan,
        on_delete=models.CASCADE,
        related_name="technical_plans",
    )

    # ------------------------------------------------------------------
    # Activité
    # ------------------------------------------------------------------

    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="technical_plans",
    )

    # ------------------------------------------------------------------
    # Quantité prévue
    # ------------------------------------------------------------------

    planned_quantity = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # ------------------------------------------------------------------
    # Unité de mesure
    #
    # Conservée ici également car l'unité utilisée dans une programmation
    # annuelle peut être précisée au niveau du PTBA.
    # ------------------------------------------------------------------

    unit = models.ForeignKey(
        "core.UnitOfMeasure",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="technical_plans",
    )

    # ------------------------------------------------------------------
    # Zone d'intervention programmée
    # ------------------------------------------------------------------

    geo_unit = models.ForeignKey(
        "geo.GeoUnit",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="technical_plans",
    )

    # ------------------------------------------------------------------
    # Responsable PTBA
    # ------------------------------------------------------------------

    responsible = models.ForeignKey(
        "core.Partner",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="technical_plans",
    )

    # ------------------------------------------------------------------
    # Période prévue
    # ------------------------------------------------------------------

    planned_start_date = models.DateField(
        null=True,
        blank=True,
    )

    planned_end_date = models.DateField(
        null=True,
        blank=True,
    )

    # ------------------------------------------------------------------
    # Modalités de mise en œuvre
    # ------------------------------------------------------------------

    implementation_modality = models.TextField(
        blank=True,
    )

    # ------------------------------------------------------------------
    # Extrant attendu
    # ------------------------------------------------------------------

    expected_output = models.TextField(
        blank=True,
    )

    # ------------------------------------------------------------------
    # Observations PTBA
    # ------------------------------------------------------------------

    observations = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = [
            "workplan__year",
            "activity__code",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "workplan",
                    "activity",
                ],
                name="unique_activity_per_workplan",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "project",
                    "workplan",
                ]
            ),
            models.Index(fields=["activity"]),
            models.Index(fields=["geo_unit"]),
            models.Index(fields=["responsible"]),
        ]

    def clean(self):
        super().clean()

        # --------------------------------------------------------------
        # PTBA du même projet
        # --------------------------------------------------------------

        if self.workplan_id:
            if self.workplan.project_id != self.project_id:
                raise ValidationError({
                    "workplan":
                    "Le PTBA doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # Activité du même projet
        # --------------------------------------------------------------

        if self.activity_id:
            if self.activity.project_id != self.project_id:
                raise ValidationError({
                    "activity":
                    "L'activité doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # Zone du même projet
        # --------------------------------------------------------------

        if self.geo_unit_id:
            if self.geo_unit.project_id != self.project_id:
                raise ValidationError({
                    "geo_unit":
                    "La zone d'intervention doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # Responsable du même projet
        # --------------------------------------------------------------

        if self.responsible_id:
            if self.responsible.project_id != self.project_id:
                raise ValidationError({
                    "responsible":
                    "Le responsable doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # Unité du même projet
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

        if self.planned_start_date and self.planned_end_date:
            if self.planned_end_date < self.planned_start_date:
                raise ValidationError({
                    "planned_end_date":
                    "La date prévue de fin ne peut pas être antérieure "
                    "à la date prévue de début."
                })

    def __str__(self):
        return f"{self.workplan} — {self.activity}"


# ======================================================================
# CALENDRIER MENSUEL DU PTBA
# ======================================================================

class TechnicalSchedule(ProjectOwnedModel):
    """
    Calendrier mensuel d'une programmation technique.

    Permet de reproduire le chronogramme Janvier -> Décembre du PTBA
    sans créer douze colonnes dans Activity.
    """

    class Month(models.IntegerChoices):
        JANUARY = 1, "Janvier"
        FEBRUARY = 2, "Février"
        MARCH = 3, "Mars"
        APRIL = 4, "Avril"
        MAY = 5, "Mai"
        JUNE = 6, "Juin"
        JULY = 7, "Juillet"
        AUGUST = 8, "Août"
        SEPTEMBER = 9, "Septembre"
        OCTOBER = 10, "Octobre"
        NOVEMBER = 11, "Novembre"
        DECEMBER = 12, "Décembre"

    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="technical_schedules",
    )

    technical_plan = models.ForeignKey(
        TechnicalPlan,
        on_delete=models.CASCADE,
        related_name="schedule",
    )

    month = models.PositiveSmallIntegerField(
        choices=Month.choices,
    )

    is_planned = models.BooleanField(
        default=True,
    )

    planned_quantity = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
    )

    note = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = [
            "technical_plan",
            "month",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "technical_plan",
                    "month",
                ],
                name="unique_month_per_technical_plan",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "project",
                    "technical_plan",
                ]
            ),
            models.Index(fields=["month"]),
        ]

    def clean(self):
        super().clean()

        if self.technical_plan_id:
            if self.technical_plan.project_id != self.project_id:
                raise ValidationError({
                    "technical_plan":
                    "La programmation technique doit appartenir au même projet."
                })

    def __str__(self):
        return (
            f"{self.technical_plan.activity} — "
            f"{self.get_month_display()}"
        )


# ======================================================================
# PARTICIPANTS
# ======================================================================

class ActivityParticipant(models.Model):
    """
    Structure existante conservée.

    Elle pourra être réévaluée plus tard lors du traitement
    du suivi de l'exécution technique.
    """

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