from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import BaseModel


class GeoLevel(BaseModel):
    """
    Niveau géographique paramétrable du projet.

    Exemples pour PRDC-VFS :
    0 = Pays
    1 = Wilaya
    2 = Moughataa
    3 = Commune
    4 = Village / Localité

    La structure reste générique afin de permettre
    son utilisation par d'autres projets.
    """

    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="geo_levels",
    )

    name = models.CharField(
        max_length=120,
    )

    name_plural = models.CharField(
        max_length=120,
        blank=True,
    )

    rank = models.PositiveIntegerField(
        help_text="0 = top level",
    )

    code = models.CharField(
        max_length=32,
    )

    class Meta:
        unique_together = [
            ("project", "rank"),
            ("project", "code"),
        ]

        ordering = [
            "rank",
        ]

    def __str__(self):
        return f"{self.name} ({self.rank})"


class GeoUnit(BaseModel):
    """
    Unité géographique appartenant à un niveau.

    Exemple PRDC-VFS :

    Mauritanie
        └── Trarza
            └── Mederdra
                └── Commune X
                    └── Village Y

    Une activité peut ensuite être rattachée directement
    à n'importe quel GeoUnit :
    Wilaya, Moughataa, Commune ou Village.
    """

    project = models.ForeignKey(
        "core.Project",
        on_delete=models.CASCADE,
        related_name="geo_units",
    )

    geo_level = models.ForeignKey(
        GeoLevel,
        on_delete=models.PROTECT,
        related_name="units",
    )

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )

    name = models.CharField(
        max_length=255,
    )

    code = models.CharField(
        max_length=64,
    )

    population = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    latitude = models.FloatField(
        null=True,
        blank=True,
    )

    longitude = models.FloatField(
        null=True,
        blank=True,
    )

    geojson = models.TextField(
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        unique_together = [
            ("project", "code"),
        ]

        ordering = [
            "geo_level__rank",
            "name",
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """
        Contrôles de cohérence de la hiérarchie géographique.

        Règles :
        - Le premier niveau peut ne pas avoir de parent.
        - Tous les autres niveaux doivent avoir un parent.
        - Le parent doit être exactement un niveau au-dessus.
        - Parent et enfant doivent appartenir au même projet.
        - Une unité ne peut pas être son propre parent.
        """

        # ---------------------------------------------------------
        # Le niveau géographique doit appartenir au même projet
        # ---------------------------------------------------------

        if (
            self.project_id
            and self.geo_level_id
            and self.geo_level.project_id != self.project_id
        ):
            raise ValidationError(
                {
                    "geo_level":
                        "Le niveau géographique doit appartenir au même projet."
                }
            )

        # ---------------------------------------------------------
        # Contrôles concernant le parent
        # ---------------------------------------------------------

        if self.parent_id:

            # Une unité ne peut pas être son propre parent.
            if self.pk and self.parent_id == self.pk:
                raise ValidationError(
                    {
                        "parent":
                            "Une unité géographique ne peut pas être son propre parent."
                    }
                )

            # Parent et enfant doivent appartenir au même projet.
            if (
                self.project_id
                and self.parent.project_id != self.project_id
            ):
                raise ValidationError(
                    {
                        "parent":
                            "Le parent doit appartenir au même projet."
                    }
                )

            # Le parent doit être exactement un niveau au-dessus.
            if (
                self.geo_level_id
                and self.parent.geo_level.rank
                != self.geo_level.rank - 1
            ):
                raise ValidationError(
                    {
                        "parent":
                            "Le parent doit appartenir au niveau géographique immédiatement supérieur."
                    }
                )

        # ---------------------------------------------------------
        # Une unité sans parent est autorisée uniquement au rang 0
        # ---------------------------------------------------------

        elif (
            self.geo_level_id
            and self.geo_level.rank != 0
        ):
            raise ValidationError(
                {
                    "parent":
                        "Seules les unités du niveau géographique supérieur peuvent ne pas avoir de parent."
                }
            )

    @classmethod
    def descendants_ids(cls, unit):
        """
        Retourne l'identifiant de l'unité et de tous ses descendants.

        Exemple :

        Trarza
            └── Moughataa
                └── Commune
                    └── Village

        descendants_ids(Trarza) retournera l'ensemble
        Trarza + Moughataas + Communes + Villages.

        Cette méthode est importante pour les filtres,
        rapports et contrôles d'accès territoriaux.
        """

        if unit is None:
            return set()

        ids = {
            unit.id,
        }

        frontier = [
            unit.id,
        ]

        while frontier:

            children = list(
                cls.objects.filter(
                    parent_id__in=frontier
                ).values_list(
                    "id",
                    flat=True,
                )
            )

            children = [
                child_id
                for child_id in children
                if child_id not in ids
            ]

            ids.update(
                children
            )

            frontier = children

        return ids