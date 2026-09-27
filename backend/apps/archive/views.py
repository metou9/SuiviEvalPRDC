from rest_framework.parsers import (
    FormParser,
    MultiPartParser,
)
from rest_framework.permissions import IsAuthenticated

from apps.core.api import AuthoredModelViewSet

from .models import ArchiveDocument
from .serializers import ArchiveDocumentSerializer


class ArchiveDocumentViewSet(AuthoredModelViewSet):
    serializer_class = ArchiveDocumentSerializer
    permission_classes = [IsAuthenticated]

    parser_classes = (
        MultiPartParser,
        FormParser,
    )

    queryset = (
        ArchiveDocument.objects
        .select_related(
            "project",
            "created_by",
        )
        .all()
    )

    search_fields = (
        "title",
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
    )

    ordering_fields = (
        "title",
        "created_at",
    )

    ordering = (
        "-created_at",
    )