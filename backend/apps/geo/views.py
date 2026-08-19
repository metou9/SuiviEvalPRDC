from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import ReadOrCapability
from apps.core.api import AuthoredModelViewSet, ExportMixin

from .models import GeoLevel, GeoUnit
from .serializers import (
    GeoLevelSerializer,
    GeoUnitSerializer,
    GeoUnitTreeSerializer,
)


class GeoLevelViewSet(
    ExportMixin,
    AuthoredModelViewSet,
):
    serializer_class = GeoLevelSerializer

    queryset = GeoLevel.objects.all()

    permission_classes = [
        ReadOrCapability,
    ]

    write_capability = "reference.manage"

    filterset_fields = [
        "rank",
        "code",
    ]

    search_fields = [
        "name",
        "code",
    ]

    ordering_fields = [
        "rank",
    ]

    ordering = [
        "rank",
    ]


class GeoUnitViewSet(
    ExportMixin,
    AuthoredModelViewSet,
):
    serializer_class = GeoUnitSerializer

    queryset = (
        GeoUnit.objects
        .select_related(
            "geo_level",
            "parent",
            "parent__geo_level",
        )
        .all()
    )

    permission_classes = [
        ReadOrCapability,
    ]

    write_capability = "reference.manage"

    filterset_fields = {
        "geo_level": ["exact"],
        "parent": ["exact", "isnull"],
        "is_active": ["exact"],
    }

    search_fields = [
        "name",
        "code",
    ]

    ordering_fields = [
        "name",
        "geo_level__rank",
    ]

    ordering = [
        "geo_level__rank",
        "name",
    ]

    def get_queryset(self):
        qs = super().get_queryset()

        level = self.request.query_params.get(
            "level"
        )

        if level is not None:

            # Recherche par rang :
            # ?level=0
            # ?level=1
            # ?level=2
            # etc.
            if level.isdigit():
                qs = qs.filter(
                    geo_level__rank=int(level)
                )

            # Recherche par code :
            # ?level=PAYS
            # ?level=WILAYA
            # ?level=MOUGHATAA
            # ?level=COMMUNE
            # ?level=VILLAGE
            else:
                qs = qs.filter(
                    geo_level__code=level
                )

        return qs

    def list(self, request, *args, **kwargs):
        """
        Liste classique :

        /geo-units/

        Arbre géographique :

        /geo-units/?tree=true
        """

        if request.query_params.get("tree") == "true":

            roots = (
                self.filter_queryset(
                    self.get_queryset()
                )
                .filter(
                    parent__isnull=True
                )
            )

            serializer = GeoUnitTreeSerializer(
                roots,
                many=True,
                context=self.get_serializer_context(),
            )

            return Response(
                serializer.data
            )

        return super().list(
            request,
            *args,
            **kwargs
        )

    @action(
        detail=False,
        methods=["get"],
    )
    def tree(self, request):
        """
        Retourne l'arbre géographique complet
        du projet courant.

        Exemple PRDC-VFS :

        Mauritanie
          ├── Trarza
          │     └── Moughataa
          │           └── Commune
          │                 └── Village
          │
          ├── Brakna
          ├── Gorgol
          └── Guidimagha
        """

        roots = (
            self.get_queryset()
            .filter(
                parent__isnull=True
            )
        )

        serializer = GeoUnitTreeSerializer(
            roots,
            many=True,
            context=self.get_serializer_context(),
        )

        return Response(
            serializer.data
        )