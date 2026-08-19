"""Core base classes, the Project entity, generic attachments and the workflow engine."""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Workflow state machine
# ---------------------------------------------------------------------------

class WorkflowState(models.TextChoices):
    DRAFT = "DRAFT", "Brouillon"
    SUBMITTED = "SUBMITTED", "Soumis"
    VALIDATED = "VALIDATED", "Validé"
    AUDITED = "AUDITED", "Audité"
    CONSOLIDATED = "CONSOLIDATED", "Consolidé"
    REJECTED = "REJECTED", "Rejeté"


WORKFLOW_TRANSITIONS = {
    "submit": (["DRAFT"], "SUBMITTED"),
    "validate": (["SUBMITTED"], "VALIDATED"),
    "audit": (["VALIDATED"], "AUDITED"),
    "consolidate": (["AUDITED"], "CONSOLIDATED"),
    "reject": (["SUBMITTED", "VALIDATED", "AUDITED"], "REJECTED"),
    "reopen": (["REJECTED", "CONSOLIDATED"], "DRAFT"),
}


_REJECT_CAP = {
    "SUBMITTED": "validate",
    "VALIDATED": "audit",
    "AUDITED": "consolidate",
}

_REOPEN_CAP = {
    "REJECTED": "submit",
    "CONSOLIDATED": "consolidate",
}


def required_capability_step(action, source_state):
    """Return the capability step (e.g. 'validate') an action requires from a state."""

    if action == "reject":
        return _REJECT_CAP.get(source_state, "consolidate")

    if action == "reopen":
        return _REOPEN_CAP.get(source_state, "consolidate")

    return action


class WorkflowError(Exception):
    """Raised when a transition is not allowed."""


# ---------------------------------------------------------------------------
# Abstract base classes
# ---------------------------------------------------------------------------

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuthoredModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        abstract = True


class BaseModel(TimeStampedModel, AuthoredModel):
    """Every domain row carries timestamps + author audit fields."""

    class Meta:
        abstract = True


class ProjectOwnedModel(BaseModel):
    """Domain rows that belong to a single project."""

    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="+",
    )

    class Meta:
        abstract = True


class WorkflowMixin(models.Model):
    """Adds a lifecycle status field and the transition engine."""

    WORKFLOW_AREA = None

    status = models.CharField(
        max_length=16,
        choices=WorkflowState.choices,
        default=WorkflowState.DRAFT,
        db_index=True,
    )

    class Meta:
        abstract = True

    def can_transition(self, action):
        spec = WORKFLOW_TRANSITIONS.get(action)
        return bool(spec) and self.status in spec[0]

    def transition(self, user, action, comment="", check_capability=True):
        """Validate + apply a workflow action, writing a StateEvent."""

        from apps.accounts.capabilities import has_capability

        spec = WORKFLOW_TRANSITIONS.get(action)

        if not spec:
            raise WorkflowError(f"Unknown action '{action}'.")

        sources, target = spec

        if self.status not in sources:
            raise WorkflowError(
                f"Cannot '{action}' from state '{self.status}'."
            )

        if check_capability:
            step = required_capability_step(action, self.status)
            capability = f"{self.WORKFLOW_AREA}.{step}"

            if not has_capability(user, capability, obj=self):
                raise WorkflowError(
                    f"User lacks capability '{capability}' for this record."
                )

        from_state = self.status
        self.status = target

        self.updated_by = (
            user if user and user.is_authenticated else None
        )

        self.save(
            update_fields=[
                "status",
                "updated_by",
                "updated_at",
            ]
        )

        return StateEvent.objects.create(
            content_object=self,
            from_state=from_state,
            to_state=target,
            action=action,
            actor=user if user and user.is_authenticated else None,
            comment=comment or "",
        )


# ---------------------------------------------------------------------------
# Project & milestones
# ---------------------------------------------------------------------------

class Project(BaseModel):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)

    currency_code = models.CharField(
        max_length=8,
        default="MRU",
    )

    currency_symbol = models.CharField(
        max_length=8,
        default="UM",
    )

    start_date = models.DateField(
        null=True,
        blank=True,
    )

    closing_date = models.DateField(
        null=True,
        blank=True,
    )

    fiscal_year_start_month = models.PositiveSmallIntegerField(
        default=1,
    )

    country = models.CharField(
        max_length=120,
        blank=True,
    )

    funder = models.CharField(
        max_length=255,
        blank=True,
    )

    logo = models.ImageField(
        upload_to="project_logos/",
        null=True,
        blank=True,
    )

    default_locale = models.CharField(
        max_length=8,
        default="fr",
    )

    grievance_sla_days = models.PositiveIntegerField(
        default=30,
    )

    public_dashboards_enabled = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return self.name


class Milestone(BaseModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="milestones",
    )

    code = models.CharField(
        max_length=32,
    )

    name = models.CharField(
        max_length=255,
    )

    target_date = models.DateField(
        null=True,
        blank=True,
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
        return f"{self.code} — {self.name}"


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

class UnitOfMeasure(ProjectOwnedModel):
    """
    Unité de mesure.
    """

    code = models.CharField(
        max_length=32,
    )

    name = models.CharField(
        max_length=255,
    )

    symbol = models.CharField(
        max_length=32,
        blank=True,
    )

    class Meta:
        unique_together = [
            ("project", "code"),
        ]

        ordering = [
            "name",
        ]

        indexes = [
            models.Index(fields=["project", "code"]),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Actor(ProjectOwnedModel):
    """
    Acteur intervenant dans le projet.
    """

    code = models.CharField(
        max_length=32,
    )

    name = models.CharField(
        max_length=255,
    )

    level = models.CharField(
        max_length=100,
    )

    phone = models.CharField(
        max_length=50,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    class Meta:
        unique_together = [
            ("project", "code"),
        ]

        ordering = [
            "name",
        ]

        indexes = [
            models.Index(fields=["project", "code"]),
            models.Index(fields=["level"]),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Partner(ProjectOwnedModel):
    """
    Responsable / Partenaire du projet.
    """

    code = models.CharField(
        max_length=32,
    )

    name = models.CharField(
        max_length=255,
    )

    phone = models.CharField(
        max_length=50,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    class Meta:
        unique_together = [
            ("project", "code"),
        ]

        ordering = [
            "name",
        ]

        indexes = [
            models.Index(fields=["project", "code"]),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"


# ---------------------------------------------------------------------------
# Generic attachments and workflow audit trail
# ---------------------------------------------------------------------------

class Attachment(BaseModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="attachments",
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )

    object_id = models.PositiveIntegerField()

    content_object = GenericForeignKey(
        "content_type",
        "object_id",
    )

    file = models.FileField(
        upload_to="attachments/%Y/%m/",
    )

    label = models.CharField(
        max_length=255,
        blank=True,
    )

    uploaded_at = models.DateTimeField(
        default=timezone.now,
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["content_type", "object_id"]
            ),
        ]


class StateEvent(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )

    object_id = models.PositiveIntegerField()

    content_object = GenericForeignKey(
        "content_type",
        "object_id",
    )

    from_state = models.CharField(
        max_length=16,
        blank=True,
    )

    to_state = models.CharField(
        max_length=16,
    )

    action = models.CharField(
        max_length=32,
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="state_events",
    )

    at = models.DateTimeField(
        auto_now_add=True,
    )

    comment = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = [
            "at",
        ]

        indexes = [
            models.Index(
                fields=["content_type", "object_id"]
            ),
        ]

    def __str__(self):
        return f"{self.action}: {self.from_state}→{self.to_state}"


# ---------------------------------------------------------------------------
# Generic CRUD audit trail
# ---------------------------------------------------------------------------

class AuditLog(models.Model):
    """
    Journal générique des créations, modifications et suppressions.

    Il est distinct de StateEvent :
    - StateEvent = transitions de workflow.
    - AuditLog = CRUD sur les données.
    """

    class Action(models.TextChoices):
        CREATE = "CREATE", "Création"
        UPDATE = "UPDATE", "Modification"
        DELETE = "DELETE", "Suppression"

    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )

    content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    object_repr = models.CharField(
        max_length=500,
        blank=True,
    )

    action = models.CharField(
        max_length=16,
        choices=Action.choices,
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )

    at = models.DateTimeField(
        auto_now_add=True,
    )

    changes = models.JSONField(
        default=dict,
        blank=True,
    )

    class Meta:
        ordering = [
            "-at",
        ]

        indexes = [
            models.Index(
                fields=["content_type", "object_id"]
            ),
            models.Index(
                fields=["project", "at"]
            ),
            models.Index(
                fields=["actor", "at"]
            ),
            models.Index(
                fields=["action", "at"]
            ),
        ]

    def __str__(self):
        return f"{self.action} — {self.object_repr}"