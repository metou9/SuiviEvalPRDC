from django.core.exceptions import ValidationError
from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import BaseModel, ProjectOwnedModel, WorkflowMixin


# ======================================================================
# CATEGORIES DE DEPENSES
# ======================================================================

class ExpenseCategory(BaseModel):
    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="expense_categories",
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
# SOURCES DE FINANCEMENT
# ======================================================================

class FundingSource(BaseModel):
    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="funding_sources",
    )

    code = models.CharField(
        max_length=32,
    )

    name = models.CharField(
        max_length=255,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        unique_together = [
            ("project", "code"),
        ]

        ordering = [
            "code",
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"


# ======================================================================
# PROGRAMMATION FINANCIERE / LIGNE BUDGETAIRE
# ======================================================================

class BudgetLine(ProjectOwnedModel):
    """
    Programmation financière d'une activité.

    Une ligne budgétaire peut être rattachée à une activité existante.

    La structure existante est conservée :
    - sous-composante / program_node
    - catégorie de dépense
    - zone
    - source de financement
    - exercice
    - montant
    - observation

    Le lien direct avec Activity permet d'associer clairement
    la programmation financière à l'activité concernée.
    """

    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="budget_lines",
    )

    # ------------------------------------------------------------------
    # ACTIVITE
    # ------------------------------------------------------------------

    activity = models.ForeignKey(
        "activities.Activity",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="budget_lines",
    )

    # ------------------------------------------------------------------
    # SOUS-COMPOSANTE / NOEUD PROGRAMMATIQUE
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
    # ------------------------------------------------------------------

    expense_category = models.ForeignKey(
        ExpenseCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="budget_lines",
    )

    # ------------------------------------------------------------------
    # ZONE D'INTERVENTION
    #
    # geo_unit = NULL signifie :
    # programmation globale sur l'ensemble du projet.
    # ------------------------------------------------------------------

    geo_unit = models.ForeignKey(
        "geo.GeoUnit",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # ------------------------------------------------------------------
    # SOURCE DE FINANCEMENT
    # ------------------------------------------------------------------

    funding_source = models.ForeignKey(
        FundingSource,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # ------------------------------------------------------------------
    # EXERCICE
    # ------------------------------------------------------------------

    fiscal_year = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    # ------------------------------------------------------------------
    # MONTANT PROGRAMME
    # ------------------------------------------------------------------

    amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
    )

    # ------------------------------------------------------------------
    # OBSERVATION
    # ------------------------------------------------------------------

    note = models.CharField(
        max_length=500,
        blank=True,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "project",
                    "fiscal_year",
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
                    "expense_category",
                ]
            ),
            models.Index(
                fields=[
                    "funding_source",
                ]
            ),
            models.Index(
                fields=[
                    "geo_unit",
                ]
            ),
        ]

    def clean(self):
        super().clean()

        # --------------------------------------------------------------
        # ACTIVITE DU MEME PROJET
        # --------------------------------------------------------------

        if self.activity_id:
            if self.activity.project_id != self.project_id:
                raise ValidationError({
                    "activity":
                    "L'activité doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # SOUS-COMPOSANTE DU MEME PROJET
        # --------------------------------------------------------------

        if self.program_node_id:
            if self.program_node.project_id != self.project_id:
                raise ValidationError({
                    "program_node":
                    "La sous-composante doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # COHERENCE ACTIVITE / SOUS-COMPOSANTE
        # --------------------------------------------------------------

        if self.activity_id and self.program_node_id:
            if (
                self.activity.program_node_id
                and self.activity.program_node_id != self.program_node_id
            ):
                raise ValidationError({
                    "program_node":
                    "La sous-composante doit correspondre à celle de l'activité."
                })

        # --------------------------------------------------------------
        # CATEGORIE DE DEPENSE DU MEME PROJET
        # --------------------------------------------------------------

        if self.expense_category_id:
            if self.expense_category.project_id != self.project_id:
                raise ValidationError({
                    "expense_category":
                    "La catégorie de dépense doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # ZONE DU MEME PROJET
        # --------------------------------------------------------------

        if self.geo_unit_id:
            if self.geo_unit.project_id != self.project_id:
                raise ValidationError({
                    "geo_unit":
                    "La zone d'intervention doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # SOURCE DE FINANCEMENT DU MEME PROJET
        # --------------------------------------------------------------

        if self.funding_source_id:
            if self.funding_source.project_id != self.project_id:
                raise ValidationError({
                    "funding_source":
                    "La source de financement doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # EXERCICE
        # --------------------------------------------------------------

        if self.fiscal_year is not None:
            if self.fiscal_year < 2010 or self.fiscal_year > 2090:
                raise ValidationError({
                    "fiscal_year":
                    "L'exercice doit être compris entre 2010 et 2090."
                })

        # --------------------------------------------------------------
        # MONTANT
        # --------------------------------------------------------------

        if self.amount is not None and self.amount < 0:
            raise ValidationError({
                "amount":
                "Le montant programmé ne peut pas être négatif."
            })

    def __str__(self):
        if self.activity:
            return (
                f"{self.activity} — "
                f"{self.amount} "
                f"({self.fiscal_year or 'LOP'})"
            )

        return (
            f"Budget {self.amount} "
            f"({self.fiscal_year or 'LOP'})"
        )


# ======================================================================
# EXECUTION FINANCIERE / TRANSACTIONS
# ======================================================================

class FinancialTransaction(WorkflowMixin, ProjectOwnedModel):
    WORKFLOW_AREA = "financialtransaction"

    class Kind(models.TextChoices):
        ENGAGEMENT = "ENGAGEMENT", "Engagement"
        DISBURSEMENT = "DISBURSEMENT", "Décaissement"
        REALIZATION = "REALIZATION", "Réalisation"

    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="financial_transactions",
    )

    # ------------------------------------------------------------------
    # LIGNE BUDGETAIRE / PROGRAMMATION FINANCIERE
    # ------------------------------------------------------------------

    budget_line = models.ForeignKey(
        BudgetLine,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="transactions",
    )

    # ------------------------------------------------------------------
    # SOUS-COMPOSANTE
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
    # ------------------------------------------------------------------

    expense_category = models.ForeignKey(
        ExpenseCategory,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="transactions",
    )

    # ------------------------------------------------------------------
    # ZONE
    # ------------------------------------------------------------------

    geo_unit = models.ForeignKey(
        "geo.GeoUnit",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # ------------------------------------------------------------------
    # SOURCE DE FINANCEMENT
    # ------------------------------------------------------------------

    funding_source = models.ForeignKey(
        FundingSource,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # ------------------------------------------------------------------
    # TYPE DE TRANSACTION
    # ------------------------------------------------------------------

    kind = models.CharField(
        max_length=16,
        choices=Kind.choices,
    )

    # ------------------------------------------------------------------
    # DATE
    # ------------------------------------------------------------------

    date = models.DateField()

    # ------------------------------------------------------------------
    # EXERCICE
    # ------------------------------------------------------------------

    fiscal_year = models.PositiveIntegerField()

    # ------------------------------------------------------------------
    # MONTANT
    # ------------------------------------------------------------------

    amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
    )

    # ------------------------------------------------------------------
    # REFERENCE
    # ------------------------------------------------------------------

    reference = models.CharField(
        max_length=255,
        blank=True,
    )

    # ------------------------------------------------------------------
    # DESCRIPTION / LIBELLE
    # ------------------------------------------------------------------

    narrative = models.TextField(
        blank=True,
    )

    # ------------------------------------------------------------------
    # PIECE JUSTIFICATIVE
    # ------------------------------------------------------------------

    supporting_doc = models.FileField(
        upload_to="finance_docs/%Y/%m/",
        null=True,
        blank=True,
    )

    # ------------------------------------------------------------------
    # HISTORIQUE
    # ------------------------------------------------------------------

    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "project",
                    "kind",
                    "fiscal_year",
                ]
            ),
            models.Index(
                fields=[
                    "budget_line",
                ]
            ),
            models.Index(
                fields=[
                    "expense_category",
                ]
            ),
            models.Index(
                fields=[
                    "program_node",
                ]
            ),
            models.Index(
                fields=[
                    "status",
                ]
            ),
        ]

        ordering = [
            "-date",
        ]

    # ==================================================================
    # VALIDATION
    # ==================================================================

    def clean(self):
        super().clean()

        # --------------------------------------------------------------
        # LIGNE BUDGETAIRE DU MEME PROJET
        # --------------------------------------------------------------

        if self.budget_line_id:
            if self.budget_line.project_id != self.project_id:
                raise ValidationError({
                    "budget_line":
                    "La ligne budgétaire doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # SOUS-COMPOSANTE DU MEME PROJET
        # --------------------------------------------------------------

        if self.program_node_id:
            if self.program_node.project_id != self.project_id:
                raise ValidationError({
                    "program_node":
                    "La sous-composante doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # CATEGORIE DE DEPENSE DU MEME PROJET
        # --------------------------------------------------------------

        if self.expense_category_id:
            if self.expense_category.project_id != self.project_id:
                raise ValidationError({
                    "expense_category":
                    "La catégorie de dépense doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # ZONE DU MEME PROJET
        # --------------------------------------------------------------

        if self.geo_unit_id:
            if self.geo_unit.project_id != self.project_id:
                raise ValidationError({
                    "geo_unit":
                    "La zone doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # SOURCE DE FINANCEMENT DU MEME PROJET
        # --------------------------------------------------------------

        if self.funding_source_id:
            if self.funding_source.project_id != self.project_id:
                raise ValidationError({
                    "funding_source":
                    "La source de financement doit appartenir au même projet."
                })

        # --------------------------------------------------------------
        # EXERCICE
        # --------------------------------------------------------------

        if self.fiscal_year < 2010 or self.fiscal_year > 2090:
            raise ValidationError({
                "fiscal_year":
                "L'exercice doit être compris entre 2010 et 2090."
            })

        # --------------------------------------------------------------
        # MONTANT
        # --------------------------------------------------------------

        if self.amount is not None and self.amount < 0:
            raise ValidationError({
                "amount":
                "Le montant ne peut pas être négatif."
            })

        # --------------------------------------------------------------
        # COHERENCE AVEC LA LIGNE BUDGETAIRE
        # --------------------------------------------------------------

        if self.budget_line_id:
            budget_line = self.budget_line

            # Exercice
            if (
                budget_line.fiscal_year is not None
                and self.fiscal_year != budget_line.fiscal_year
            ):
                raise ValidationError({
                    "fiscal_year":
                    "L'exercice de la transaction doit correspondre "
                    "à l'exercice de la ligne budgétaire."
                })

            # Sous-composante
            if (
                self.program_node_id
                and budget_line.program_node_id
                and self.program_node_id != budget_line.program_node_id
            ):
                raise ValidationError({
                    "program_node":
                    "La sous-composante doit correspondre "
                    "à celle de la ligne budgétaire."
                })

            # Catégorie de dépense
            if (
                self.expense_category_id
                and budget_line.expense_category_id
                and self.expense_category_id
                != budget_line.expense_category_id
            ):
                raise ValidationError({
                    "expense_category":
                    "La catégorie de dépense doit correspondre "
                    "à celle de la ligne budgétaire."
                })

            # Source de financement
            if (
                self.funding_source_id
                and budget_line.funding_source_id
                and self.funding_source_id
                != budget_line.funding_source_id
            ):
                raise ValidationError({
                    "funding_source":
                    "La source de financement doit correspondre "
                    "à celle de la ligne budgétaire."
                })

            # Zone
            if (
                self.geo_unit_id
                and budget_line.geo_unit_id
                and self.geo_unit_id != budget_line.geo_unit_id
            ):
                raise ValidationError({
                    "geo_unit":
                    "La zone doit correspondre "
                    "à celle de la ligne budgétaire."
                })

    def __str__(self):
        return (
            f"{self.kind} "
            f"{self.amount} "
            f"({self.fiscal_year})"
        )