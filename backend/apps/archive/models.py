from django.db import models

from apps.core.models import ProjectOwnedModel


class ArchiveDocument(ProjectOwnedModel):
    """
    Document de l'archivage électronique.

    Le modèle ProjectOwnedModel fournit déjà :
    - project
    - created_at
    - updated_at
    - created_by
    - updated_by
    """

    title = models.CharField(
        max_length=255,
        verbose_name="Titre du document",
    )

    file = models.FileField(
        upload_to="archive/%Y/%m/",
        verbose_name="Document",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Document archivé"
        verbose_name_plural = "Documents archivés"

    def __str__(self):
        return self.title