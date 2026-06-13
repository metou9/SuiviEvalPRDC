from rest_framework import serializers

from .models import GrievanceType


class GrievanceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrievanceType
        fields = ["id", "project", "code", "name", "sla_days", "is_active"]
        read_only_fields = ["project"]
