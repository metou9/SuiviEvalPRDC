from django.db import models

from apps.core.models import BaseModel


class ProgramNode(BaseModel):
    class NodeType(models.TextChoices):
        COMPONENT = "COMPONENT", "Composante"
        SUBCOMPONENT = "SUBCOMPONENT", "Sous-composante"
        ACTION = "ACTION", "Action"
        OTHER = "OTHER", "Autre"

    project = models.ForeignKey(
        "core.Project", on_delete=models.CASCADE, related_name="program_nodes"
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    node_type = models.CharField(max_length=16, choices=NodeType.choices, default=NodeType.COMPONENT)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("project", "code")]
        ordering = ["order", "code"]

    def __str__(self):
        return f"{self.code} — {self.name}"
