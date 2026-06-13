from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import BaseModel


class GeoLevel(BaseModel):
    project = models.ForeignKey("core.Project", on_delete=models.CASCADE, related_name="geo_levels")
    name = models.CharField(max_length=120)
    name_plural = models.CharField(max_length=120, blank=True)
    rank = models.PositiveIntegerField(help_text="0 = top level")
    code = models.CharField(max_length=32)

    class Meta:
        unique_together = [("project", "rank"), ("project", "code")]
        ordering = ["rank"]

    def __str__(self):
        return f"{self.name} ({self.rank})"


class GeoUnit(BaseModel):
    project = models.ForeignKey("core.Project", on_delete=models.CASCADE, related_name="geo_units")
    geo_level = models.ForeignKey(GeoLevel, on_delete=models.PROTECT, related_name="units")
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64)
    population = models.PositiveIntegerField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    geojson = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("project", "code")]
        ordering = ["geo_level__rank", "name"]

    def __str__(self):
        return self.name

    def clean(self):
        # A unit's parent must be exactly one rank above it.
        if self.parent_id:
            if self.parent.geo_level.rank != self.geo_level.rank - 1:
                raise ValidationError(
                    "Parent geo level rank must be exactly one less than this unit's rank."
                )
        elif self.geo_level_id and self.geo_level.rank != 0:
            raise ValidationError("Only rank-0 units may have no parent.")

    @classmethod
    def descendants_ids(cls, unit):
        """Set of ids for ``unit`` and all of its descendants (inclusive)."""
        if unit is None:
            return set()
        ids = {unit.id}
        frontier = [unit.id]
        while frontier:
            children = list(
                cls.objects.filter(parent_id__in=frontier).values_list("id", flat=True)
            )
            children = [c for c in children if c not in ids]
            ids.update(children)
            frontier = children
        return ids
