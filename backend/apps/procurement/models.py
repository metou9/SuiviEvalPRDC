from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import BaseModel, ProjectOwnedModel, WorkflowMixin


class ProcurementMethod(BaseModel):
    project = models.ForeignKey(
        "core.Project", on_delete=models.CASCADE, related_name="procurement_methods"
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
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


class ProcurementStage(BaseModel):
    project = models.ForeignKey(
        "core.Project", on_delete=models.CASCADE, related_name="procurement_stages"
    )
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("project", "code")]
        ordering = ["order"]

    def __str__(self):
        return f"{self.order}. {self.name}"


class PPMItem(BaseModel):
    project = models.ForeignKey("core.Project", on_delete=models.CASCADE, related_name="ppm_items")
    ppm_ref = models.CharField(max_length=64, blank=True)
    designation = models.CharField(max_length=500)
    program_node = models.ForeignKey(
        "program.ProgramNode", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    expense_category = models.ForeignKey(
        "finance.ExpenseCategory", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    procurement_method = models.ForeignKey(
        ProcurementMethod, null=True, blank=True, on_delete=models.SET_NULL, related_name="ppm_items"
    )
    planned_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    planned_year = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.designation


class ProcurementProcess(WorkflowMixin, ProjectOwnedModel):
    WORKFLOW_AREA = "procurementprocess"

    project = models.ForeignKey(
        "core.Project", on_delete=models.CASCADE, related_name="procurement_processes"
    )
    ppm_item = models.ForeignKey(
        PPMItem, null=True, blank=True, on_delete=models.SET_NULL, related_name="processes"
    )
    designation = models.CharField(max_length=500)
    procurement_method = models.ForeignKey(
        ProcurementMethod, null=True, blank=True, on_delete=models.SET_NULL, related_name="processes"
    )
    expense_category = models.ForeignKey(
        "finance.ExpenseCategory", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    program_node = models.ForeignKey(
        "program.ProgramNode", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    geo_unit = models.ForeignKey(
        "geo.GeoUnit", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    estimated_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    awarded_amount = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    supplier = models.CharField(max_length=255, blank=True)
    current_stage = models.ForeignKey(
        ProcurementStage, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    is_completed = models.BooleanField(default=False)
    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["procurement_method"]),
            models.Index(fields=["current_stage"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.designation


class StageEvent(models.Model):
    procurement_process = models.ForeignKey(
        ProcurementProcess, on_delete=models.CASCADE, related_name="stage_events"
    )
    procurement_stage = models.ForeignKey(
        ProcurementStage, on_delete=models.CASCADE, related_name="+"
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    decision = models.CharField(max_length=500, blank=True)
    deadline = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["procurement_stage__order"]

    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return None
