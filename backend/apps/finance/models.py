from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import BaseModel, ProjectOwnedModel, WorkflowMixin


class ExpenseCategory(BaseModel):
    project = models.ForeignKey(
        "core.Project", on_delete=models.CASCADE, related_name="expense_categories"
    )
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("project", "code")]
        ordering = ["order", "code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class FundingSource(BaseModel):
    project = models.ForeignKey(
        "core.Project", on_delete=models.CASCADE, related_name="funding_sources"
    )
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("project", "code")]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class BudgetLine(ProjectOwnedModel):
    project = models.ForeignKey(
        "core.Project", on_delete=models.CASCADE, related_name="budget_lines"
    )
    program_node = models.ForeignKey(
        "program.ProgramNode", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    expense_category = models.ForeignKey(
        ExpenseCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name="budget_lines"
    )
    geo_unit = models.ForeignKey(
        "geo.GeoUnit", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    funding_source = models.ForeignKey(
        FundingSource, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    fiscal_year = models.PositiveIntegerField(null=True, blank=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    note = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return f"Budget {self.amount} ({self.fiscal_year or 'LOP'})"


class FinancialTransaction(WorkflowMixin, ProjectOwnedModel):
    WORKFLOW_AREA = "financialtransaction"

    class Kind(models.TextChoices):
        ENGAGEMENT = "ENGAGEMENT", "Engagement"
        DISBURSEMENT = "DISBURSEMENT", "Décaissement"
        REALIZATION = "REALIZATION", "Réalisation"

    project = models.ForeignKey(
        "core.Project", on_delete=models.CASCADE, related_name="financial_transactions"
    )
    program_node = models.ForeignKey(
        "program.ProgramNode", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    expense_category = models.ForeignKey(
        ExpenseCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name="transactions"
    )
    geo_unit = models.ForeignKey(
        "geo.GeoUnit", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    funding_source = models.ForeignKey(
        FundingSource, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    date = models.DateField()
    fiscal_year = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    reference = models.CharField(max_length=255, blank=True)
    narrative = models.TextField(blank=True)
    supporting_doc = models.FileField(upload_to="finance_docs/%Y/%m/", null=True, blank=True)
    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=["project", "kind", "fiscal_year"]),
            models.Index(fields=["expense_category"]),
            models.Index(fields=["program_node"]),
            models.Index(fields=["status"]),
        ]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.kind} {self.amount} ({self.fiscal_year})"
