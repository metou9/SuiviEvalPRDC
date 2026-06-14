from rest_framework import serializers

from .models import ProgramNode


class ProgramNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgramNode
        fields = [
            "id", "project", "parent", "node_type", "code", "name",
            "description", "order", "is_active",
        ]
        read_only_fields = ["project"]


class ProgramNodeTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = ProgramNode
        fields = ["id", "code", "name", "node_type", "order", "is_active", "children"]

    def get_children(self, obj):
        return ProgramNodeTreeSerializer(
            obj.children.all().order_by("order", "code"), many=True
        ).data
