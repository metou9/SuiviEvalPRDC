from rest_framework import serializers

from .models import ArchiveDocument


class ArchiveDocumentSerializer(serializers.ModelSerializer):
    imported_by = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ArchiveDocument

        fields = (
            "id",
            "title",
            "file",
            "file_name",
            "file_url",
            "created_at",
            "created_by",
            "imported_by",
        )

        read_only_fields = (
            "id",
            "created_at",
            "created_by",
            "imported_by",
            "file_name",
            "file_url",
        )

    def get_imported_by(self, obj):
        if not obj.created_by:
            return "—"

        user = obj.created_by

        full_name = (
            f"{getattr(user, 'first_name', '')} "
            f"{getattr(user, 'last_name', '')}"
        ).strip()

        return (
            full_name
            or getattr(user, "username", "")
            or str(user)
        )

    def get_file_name(self, obj):
        if not obj.file:
            return None

        return obj.file.name.split("/")[-1]

    def get_file_url(self, obj):
        if not obj.file:
            return None

        request = self.context.get("request")

        if request:
            return request.build_absolute_uri(
                obj.file.url
            )

        return obj.file.url