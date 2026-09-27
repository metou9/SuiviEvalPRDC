from rest_framework import serializers

from .models import Infrastructure


class InfrastructureSerializer(serializers.ModelSerializer):
    geo_unit_name = serializers.CharField(
        source="geo_unit.name",
        read_only=True,
        default=None,
    )

    class Meta:
        model = Infrastructure
        fields = "__all__"
        read_only_fields = (
            "id",
            "project",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        )


class KoboInfrastructureImportSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):
        filename = value.name.lower()

        if not filename.endswith(".xlsx"):
            raise serializers.ValidationError(
                "Le fichier doit être un export Kobo au format .xlsx."
            )

        return value