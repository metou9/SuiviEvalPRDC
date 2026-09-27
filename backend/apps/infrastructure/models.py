from django.db import models

from apps.core.models import ProjectOwnedModel


class Infrastructure(ProjectOwnedModel):
    """
    Infrastructure provenant d'une soumission KoboToolbox.

    La saisie n'est pas réalisée manuellement dans la plateforme :
    les données sont alimentées par import Kobo.
    """

    # --------------------------------------------------------------
    # IDENTIFIANTS KOBOTOOLBOX
    # --------------------------------------------------------------

    kobo_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
    )

    kobo_uuid = models.CharField(
        max_length=255,
        db_index=True,
    )

    kobo_submission_time = models.DateTimeField(
        null=True,
        blank=True,
    )

    kobo_submitted_by = models.CharField(
        max_length=255,
        blank=True,
    )

    # --------------------------------------------------------------
    # LOCALISATION
    # --------------------------------------------------------------

    geo_unit = models.ForeignKey(
        "geo.GeoUnit",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="infrastructures",
    )

    # On conserve également les valeurs Kobo originales.
    # C'est important pour la traçabilité de l'import.
    kobo_wilaya = models.CharField(
        max_length=255,
        blank=True,
    )

    kobo_moughataa = models.CharField(
        max_length=255,
        blank=True,
    )

    kobo_commune = models.CharField(
        max_length=255,
        blank=True,
    )

    village_locality = models.CharField(
        max_length=255,
        blank=True,
    )

    gps_latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )

    gps_longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
    )

    gps_altitude = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
    )

    gps_accuracy = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        null=True,
        blank=True,
    )

    # --------------------------------------------------------------
    # INFORMATIONS GENERALES
    # --------------------------------------------------------------

    enumerator_name = models.CharField(
        max_length=255,
        blank=True,
    )

    name = models.CharField(
        max_length=500,
    )

    infrastructure_type = models.CharField(
        max_length=100,
        blank=True,
    )

    infrastructure_type_other = models.CharField(
        max_length=255,
        blank=True,
    )

    # --------------------------------------------------------------
    # VOLETS RENSEIGNES DANS KOBO
    # --------------------------------------------------------------

    has_rehabilitation = models.BooleanField(default=False)
    has_maintenance = models.BooleanField(default=False)
    has_governance = models.BooleanField(default=False)

    # --------------------------------------------------------------
    # REHABILITATION / MISE A NIVEAU
    # --------------------------------------------------------------

    intervention_type = models.CharField(
        max_length=100,
        blank=True,
    )

    intervention_type_other = models.CharField(
        max_length=255,
        blank=True,
    )

    works_completed = models.BooleanField(
        null=True,
        blank=True,
    )

    completion_date = models.DateField(
        null=True,
        blank=True,
    )

    rehab_functional = models.BooleanField(
        null=True,
        blank=True,
    )

    # --------------------------------------------------------------
    # FONCTIONNEMENT / MAINTENANCE
    # --------------------------------------------------------------

    management_structure_exists = models.BooleanField(
        null=True,
        blank=True,
    )

    management_structure_name = models.CharField(
        max_length=500,
        blank=True,
    )

    maintenance_functional = models.BooleanField(
        null=True,
        blank=True,
    )

    maintenance_last_12_months = models.BooleanField(
        null=True,
        blank=True,
    )

    # --------------------------------------------------------------
    # GOUVERNANCE / PARTICIPATION DES FEMMES
    # --------------------------------------------------------------

    committee_name = models.CharField(
        max_length=500,
        blank=True,
    )

    committee_functional = models.BooleanField(
        null=True,
        blank=True,
    )

    committee_has_women = models.BooleanField(
        null=True,
        blank=True,
    )

    committee_members_total = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    committee_women_total = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    # select_multiple Kobo : on garde toutes les valeurs
    women_functions = models.JSONField(
        default=list,
        blank=True,
    )

    women_functions_other = models.CharField(
        max_length=255,
        blank=True,
    )

    class Meta:
        ordering = ["-kobo_submission_time", "-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["project", "kobo_uuid"],
                name="unique_infrastructure_kobo_uuid_project",
            ),
        ]

        indexes = [
            models.Index(fields=["project", "kobo_uuid"]),
            models.Index(fields=["geo_unit"]),
            models.Index(fields=["infrastructure_type"]),
        ]

    def __str__(self):
        return self.name or self.kobo_uuid


class InfrastructureMaintenance(ProjectOwnedModel):
    """
    Une ligne = une opération de maintenance Kobo.

    Les répétitions Kobo sont donc conservées individuellement.
    """

    infrastructure = models.ForeignKey(
        Infrastructure,
        on_delete=models.CASCADE,
        related_name="maintenances",
    )

    maintenance_date = models.DateField(
        null=True,
        blank=True,
    )

    maintenance_type = models.CharField(
        max_length=100,
        blank=True,
    )

    maintenance_type_other = models.CharField(
        max_length=500,
        blank=True,
    )

    # Identifiant de la répétition Kobo si disponible
    kobo_uuid = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-maintenance_date", "id"]

        indexes = [
            models.Index(fields=["project", "infrastructure"]),
        ]

    def __str__(self):
        return f"{self.infrastructure} - {self.maintenance_date or 'Maintenance'}"


class InfrastructurePhoto(ProjectOwnedModel):
    """Photo associée à une infrastructure Kobo."""

    infrastructure = models.ForeignKey(
        Infrastructure,
        on_delete=models.CASCADE,
        related_name="photos",
    )

    file = models.FileField(
        upload_to="infrastructure/photos/%Y/%m/",
        null=True,
        blank=True,
    )

    # Nom original du fichier dans Kobo
    kobo_filename = models.CharField(
        max_length=500,
        blank=True,
    )

    # URL/référence originale si elle existe dans l'export Kobo
    kobo_url = models.TextField(
        blank=True,
    )

    caption = models.CharField(
        max_length=500,
        blank=True,
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.kobo_filename or f"Photo {self.pk}"


class InfrastructureVideo(ProjectOwnedModel):
    """Vidéo associée à une infrastructure Kobo."""

    infrastructure = models.ForeignKey(
        Infrastructure,
        on_delete=models.CASCADE,
        related_name="videos",
    )

    file = models.FileField(
        upload_to="infrastructure/videos/%Y/%m/",
        null=True,
        blank=True,
    )

    kobo_filename = models.CharField(
        max_length=500,
        blank=True,
    )

    kobo_url = models.TextField(
        blank=True,
    )

    caption = models.CharField(
        max_length=500,
        blank=True,
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.kobo_filename or f"Vidéo {self.pk}"