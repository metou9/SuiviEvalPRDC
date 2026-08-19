from rest_framework import serializers

from .models import ProgramNode


class ProgramNodeSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(
        source="parent.name",
        read_only=True,
    )

    class Meta:
        model = ProgramNode
        fields = [
            "id",
            "project",
            "parent",
            "parent_name",
            "node_type",
            "code",
            "name",
            "description",
            "order",
        ]
        read_only_fields = ["project"]

    def validate(self, attrs):
        instance = self.instance

        node_type = attrs.get(
            "node_type",
            getattr(instance, "node_type", ProgramNode.NodeType.COMPONENT),
        )

        parent = attrs.get(
            "parent",
            getattr(instance, "parent", None),
        )

        # Une composante ne doit pas avoir de parent.
        if node_type == ProgramNode.NodeType.COMPONENT:
            if parent is not None:
                raise serializers.ValidationError({
                    "parent": "Une composante ne peut pas avoir de composante parente."
                })

        # Une sous-composante doit obligatoirement avoir une composante parente.
        if node_type == ProgramNode.NodeType.SUBCOMPONENT:
            if parent is None:
                raise serializers.ValidationError({
                    "parent": "Une sous-composante doit avoir une composante parente."
                })

            if parent.node_type != ProgramNode.NodeType.COMPONENT:
                raise serializers.ValidationError({
                    "parent": "Le parent doit être une composante."
                })

            project = self.context["request"].project

            if parent.project_id != project.id:
                raise serializers.ValidationError({
                    "parent": "La composante parente doit appartenir au même projet."
                })

        return attrs


class ProgramNodeTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = ProgramNode
        fields = [
            "id",
            "code",
            "name",
            "node_type",
            "order",
            "children",
        ]

    def get_children(self, obj):
        return ProgramNodeTreeSerializer(
            obj.children.all().order_by("order", "code"),
            many=True,
        ).data