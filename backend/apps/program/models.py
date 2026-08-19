from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import BaseModel


class ProgramNode(BaseModel):
    class NodeType(models.TextChoices):
        COMPONENT = "COMPONENT", "Composante"
        SUBCOMPONENT = "SUBCOMPONENT", "Sous-composante"

    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="program_nodes",
    )

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )

    node_type = models.CharField(
        max_length=16,
        choices=NodeType.choices,
        default=NodeType.COMPONENT,
    )

    code = models.CharField(
        max_length=64,
    )

    name = models.CharField(
        max_length=500,
    )

    # Conservé pour une éventuelle utilisation future.
    # Ce champ ne sera pas affiché dans le formulaire actuel.
    description = models.TextField(
        null=True,
        blank=True,
        default=None,
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
            "code",
        ]

    def clean(self):
        super().clean()

        # Une composante ne doit pas avoir de parent.
        if self.node_type == self.NodeType.COMPONENT:
            if self.parent_id is not None:
                raise ValidationError({
                    "parent": "Une composante ne peut pas avoir de composante parente."
                })

        # Une sous-composante doit obligatoirement avoir une composante parente.
        if self.node_type == self.NodeType.SUBCOMPONENT:
            if self.parent_id is None:
                raise ValidationError({
                    "parent": "Une sous-composante doit avoir une composante parente."
                })

            if self.parent.node_type != self.NodeType.COMPONENT:
                raise ValidationError({
                    "parent": "Le parent d'une sous-composante doit être une composante."
                })

            # Protection supplémentaire :
            # la composante et la sous-composante doivent appartenir au même projet.
            if self.parent.project_id != self.project_id:
                raise ValidationError({
                    "parent": "La composante parente doit appartenir au même projet."
                })

    def __str__(self):
        return f"{self.code} — {self.name}"