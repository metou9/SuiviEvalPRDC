from django.core.exceptions import ValidationError
from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import BaseModel, ProjectOwnedModel, WorkflowMixin


# ======================================================================
# METHODES DE PASSATION
# ======================================================================

class ProcurementMethod(BaseModel):
    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="procurement_methods",
    )

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )

    code = models.CharField(
        max_length=32,
    )

    name = models.CharField(
        max_length=255,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        unique_together = [
            ("project", "code"),
        ]

        ordering = [
            "order",
            "code",
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"


# ======================================================================
# ETAPES DE PASSATION
# ======================================================================

class ProcurementStage(BaseModel):
    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="procurement_stages",
    )

    code = models.CharField(
        max_length=32,
    )

    name = models.CharField(
        max_length=255,
    )

    order = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        unique_together = [
            ("project", "code"),
        ]

        ordering = [
            "order",
        ]

    def __str__(self):
        return f"{self.order}. {self.name}"


# ======================================================================
# PROGRAMMATION DES MARCHES
# ======================================================================

class PPMItem(BaseModel):

    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="ppm_items",
    )

    # ------------------------------------------------------------------
    # REFERENCE
    # ------------------------------------------------------------------

    ppm_ref = models.CharField(
        max_length=64,
        blank=True,
    )

    # ------------------------------------------------------------------
    # ACTIVITE
    #
    # Facultative :
    # un marché peut être lié à une activité ou être indépendant.
    # ------------------------------------------------------------------

    activity = models.ForeignKey(
        "activities.Activity",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ppm_items",
    )

    # ------------------------------------------------------------------
    # INTITULE DU MARCHE
    # ------------------------------------------------------------------

    designation = models.CharField(
        max_length=500,
    )

    # ------------------------------------------------------------------
    # SOUS-COMPOSANTE
    #
    # Structure existante conservée.
    # Lorsqu'une activité est sélectionnée, elle pourra être récupérée
    # automatiquement depuis l'activité.
    # ------------------------------------------------------------------

    program_node = models.ForeignKey(
        "program.ProgramNode",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # ------------------------------------------------------------------
    # CATEGORIE DE DEPENSE
    #
    # Structure existante conservée.
    # ------------------------------------------------------------------

    expense_category = models.ForeignKey(
        "finance.ExpenseCategory",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # ------------------------------------------------------------------
    # METHODE DE PASSATION
    #
    # Structure existante conservée.
    # ------------------------------------------------------------------

    procurement_method = models.ForeignKey(
        ProcurementMethod,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ppm_items",
    )

    # ------------------------------------------------------------------
    # COUT ESTIMATIF
    # ------------------------------------------------------------------

    planned_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # ------------------------------------------------------------------
    # EXERCICE
    # ------------------------------------------------------------------

    planned_year = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    # ------------------------------------------------------------------
    # DATE PREVUE DE SIGNATURE DU CONTRAT
    # ------------------------------------------------------------------

    planned_contract_signature_date = models.DateField(
        null=True,
        blank=True,
    )

    # ------------------------------------------------------------------
    # DATE PREVUE DE FIN DU CONTRAT
    # ------------------------------------------------------------------

    planned_contract_end_date = models.DateField(
        null=True,
        blank=True,
    )

    # ------------------------------------------------------------------
    # ETAT
    # ------------------------------------------------------------------

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "project",
                    "planned_year",
                ]
            ),
            models.Index(
                fields=[
                    "activity",
                ]
            ),
            models.Index(
                fields=[
                    "program_node",
                ]
            ),
            models.Index(
                fields=[
                    "procurement_method",
                ]
            ),
        ]

        ordering = [
            "-planned_year",
            "designation",
        ]

    # ==================================================================
    # VALIDATION
    # ==================================================================

    def clean(self):
        super().clean()

        # --------------------------------------------------------------
        # ACTIVITE / PROJET
        # --------------------------------------------------------------

        if self.activity_id:
            if self.activity.project_id != self.project_id:
                raise ValidationError({
                    "activity":
                        "L'activité doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # SOUS-COMPOSANTE / PROJET
        # --------------------------------------------------------------

        if self.program_node_id:
            if self.program_node.project_id != self.project_id:
                raise ValidationError({
                    "program_node":
                        "La sous-composante doit appartenir "
                        "au même projet."
                })

        # --------------------------------------------------------------
        # ACTIVITE / SOUS-COMPOSANTE
        # --------------------------------------------------------------

        if (
            self.activity_id
            and
            self.activity.program_node_id
        ):
            if (
                self.program_node_id
                and
                self.program_node_id
                !=
                self.activity.program_node_id
            ):
                raise ValidationError({
                    "program_node":
                        "La sous-composante doit correspondre "
                        "à celle de l'activité sélectionnée."
                })

        # --------------------------------------------------------------
        # CATEGORIE DE DEPENSE / PROJET
        # --------------------------------------------------------------

        if self.expense_category_id:
            if self.expense_category.project_id != self.project_id:
                raise ValidationError({
                    "expense_category":
                        "La catégorie de dépense doit appartenir "
                        "au même projet."
                })

        # --------------------------------------------------------------
        # METHODE DE PASSATION / PROJET
        # --------------------------------------------------------------

        if self.procurement_method_id:
            if self.procurement_method.project_id != self.project_id:
                raise ValidationError({
                    "procurement_method":
                        "La méthode de passation doit appartenir "
                        "au même projet."
                })

        # --------------------------------------------------------------
        # EXERCICE
        # --------------------------------------------------------------

        if self.planned_year is not None:
            if (
                self.planned_year < 2010
                or
                self.planned_year > 2090
            ):
                raise ValidationError({
                    "planned_year":
                        "L'exercice doit être compris entre 2010 et 2090."
                })

        # --------------------------------------------------------------
        # DATES
        # --------------------------------------------------------------

        if (
            self.planned_contract_signature_date
            and
            self.planned_contract_end_date
            and
            self.planned_contract_end_date
            <
            self.planned_contract_signature_date
        ):
            raise ValidationError({
                "planned_contract_end_date":
                    "La date prévue de fin du contrat doit être "
                    "postérieure ou égale à la date prévue "
                    "de signature du contrat."
            })

    def __str__(self):
        return self.designation


# ======================================================================
# EXECUTION / SUIVI DES MARCHES
# ======================================================================

class ProcurementProcess(WorkflowMixin, ProjectOwnedModel):
    WORKFLOW_AREA = "procurementprocess"

    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="procurement_processes",
    )

    ppm_item = models.ForeignKey(
        PPMItem,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="processes",
    )

    designation = models.CharField(
        max_length=500,
    )

    procurement_method = models.ForeignKey(
        ProcurementMethod,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="processes",
    )

    expense_category = models.ForeignKey(
        "finance.ExpenseCategory",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    program_node = models.ForeignKey(
        "program.ProgramNode",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    geo_unit = models.ForeignKey(
        "geo.GeoUnit",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    estimated_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
    )

    awarded_amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
    )

    supplier = models.CharField(
        max_length=255,
        blank=True,
    )

    current_stage = models.ForeignKey(
        ProcurementStage,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    is_completed = models.BooleanField(
        default=False,
    )

    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "project",
                    "status",
                ]
            ),
            models.Index(
                fields=[
                    "procurement_method",
                ]
            ),
            models.Index(
                fields=[
                    "current_stage",
                ]
            ),
        ]

        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return self.designation


# ======================================================================
# EVENEMENTS / ETAPES D'EXECUTION DU MARCHE
# ======================================================================

class StageEvent(models.Model):

    procurement_process = models.ForeignKey(
        ProcurementProcess,
        on_delete=models.CASCADE,
        related_name="stage_events",
    )

    procurement_stage = models.ForeignKey(
        ProcurementStage,
        on_delete=models.CASCADE,
        related_name="+",
    )

    start_date = models.DateField(
        null=True,
        blank=True,
    )

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    decision = models.CharField(
        max_length=500,
        blank=True,
    )

    deadline = models.DateField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = [
            "procurement_stage__order",
        ]

    @property
    def duration_days(self):
        if (
            self.start_date
            and
            self.end_date
        ):
            return (
                self.end_date
                -
                self.start_date
            ).days

        return None