from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import ReadOrCapability
from apps.core.api import AuthoredModelViewSet, ExportMixin

from .models import ProgramNode
from .serializers import ProgramNodeSerializer, ProgramNodeTreeSerializer


class ProgramNodeViewSet(ExportMixin, AuthoredModelViewSet):
    serializer_class = ProgramNodeSerializer
    queryset = ProgramNode.objects.select_related("parent").all()
    permission_classes = [ReadOrCapability]
    write_capability = "config.manage"
    filterset_fields = {"parent": ["exact", "isnull"], "node_type": ["exact"], "is_active": ["exact"]}
    search_fields = ["code", "name"]
    ordering_fields = ["order", "code"]

    def list(self, request, *args, **kwargs):
        if request.query_params.get("tree") == "true":
            roots = self.filter_queryset(self.get_queryset()).filter(parent__isnull=True)
            return Response(ProgramNodeTreeSerializer(roots, many=True).data)
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def tree(self, request):
        roots = self.get_queryset().filter(parent__isnull=True)
        return Response(ProgramNodeTreeSerializer(roots, many=True).data)
