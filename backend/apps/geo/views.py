from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import ReadOrCapability
from apps.core.api import AuthoredModelViewSet, ExportMixin

from .models import GeoLevel, GeoUnit
from .serializers import GeoLevelSerializer, GeoUnitSerializer, GeoUnitTreeSerializer


class GeoLevelViewSet(ExportMixin, AuthoredModelViewSet):
    serializer_class = GeoLevelSerializer
    queryset = GeoLevel.objects.all()
    permission_classes = [ReadOrCapability]
    write_capability = "config.manage"
    filterset_fields = ["rank", "code"]
    search_fields = ["name", "code"]
    ordering_fields = ["rank"]
    ordering = ["rank"]


class GeoUnitViewSet(ExportMixin, AuthoredModelViewSet):
    serializer_class = GeoUnitSerializer
    queryset = GeoUnit.objects.select_related("geo_level", "parent").all()
    permission_classes = [ReadOrCapability]
    write_capability = "config.manage"
    filterset_fields = {
        "geo_level": ["exact"],
        "parent": ["exact", "isnull"],
        "is_active": ["exact"],
    }
    search_fields = ["name", "code"]
    ordering_fields = ["name", "geo_level__rank"]

    def get_queryset(self):
        qs = super().get_queryset()
        level = self.request.query_params.get("level")
        if level is not None:
            if level.isdigit():
                qs = qs.filter(geo_level__rank=int(level))
            else:
                qs = qs.filter(geo_level__code=level)
        return qs

    def list(self, request, *args, **kwargs):
        if request.query_params.get("tree") == "true":
            roots = self.filter_queryset(self.get_queryset()).filter(parent__isnull=True)
            return Response(GeoUnitTreeSerializer(roots, many=True).data)
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def tree(self, request):
        roots = self.get_queryset().filter(parent__isnull=True)
        return Response(GeoUnitTreeSerializer(roots, many=True).data)
