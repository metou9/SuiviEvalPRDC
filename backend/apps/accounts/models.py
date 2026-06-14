from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import BaseModel


class User(AbstractUser):
    phone = models.CharField(max_length=32, blank=True)
    display_name = models.CharField(max_length=255, blank=True)
    default_locale = models.CharField(max_length=8, blank=True, default="fr")

    def __str__(self):
        return self.display_name or self.username


class Role(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(default=False)

    def __str__(self):
        return self.code


class RoleAssignment(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="role_assignments")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="assignments")
    project = models.ForeignKey(
        "core.Project", on_delete=models.CASCADE, related_name="role_assignments"
    )
    scope_geo = models.ForeignKey(
        "geo.GeoUnit", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    scope_program = models.ForeignKey(
        "program.ProgramNode", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [models.Index(fields=["user", "project"])]

    def __str__(self):
        return f"{self.user} = {self.role} @ {self.project}"


class ProjectMembership(BaseModel):
    project = models.ForeignKey(
        "core.Project", on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    is_default = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("project", "user")]

    def __str__(self):
        return f"{self.user} ∈ {self.project}"
