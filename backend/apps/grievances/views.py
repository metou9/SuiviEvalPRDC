from apps.accounts.permissions import ReadOrCapability
from apps.core.api import AuthoredModelViewSet

from .models import GrievanceType
from .serializers import GrievanceTypeSerializer


class GrievanceTypeViewSet(AuthoredModelViewSet):
    """Grievance-type reference data (configuration). The Grievance record
    workflow itself is delivered in Phase 3."""
    serializer_class = GrievanceTypeSerializer
    queryset = GrievanceType.objects.all()
    permission_classes = [ReadOrCapability]
    write_capability = "config.manage"
    filterset_fields = ["code", "is_active"]
    search_fields = ["code", "name"]
