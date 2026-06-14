from rest_framework import serializers

from .models import GeoLevel, GeoUnit


class GeoLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoLevel
        fields = ["id", "project", "name", "name_plural", "rank", "code"]
        read_only_fields = ["project"]


class GeoUnitSerializer(serializers.ModelSerializer):
    geo_level_rank = serializers.IntegerField(source="geo_level.rank", read_only=True)

    class Meta:
        model = GeoUnit
        fields = [
            "id", "project", "geo_level", "geo_level_rank", "parent", "name", "code",
            "population", "latitude", "longitude", "geojson", "is_active",
        ]
        read_only_fields = ["project"]

    def validate(self, attrs):
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        geo_level = attrs.get("geo_level", getattr(self.instance, "geo_level", None))
        if geo_level is not None:
            if parent is not None:
                if parent.geo_level.rank != geo_level.rank - 1:
                    raise serializers.ValidationError(
                        {"parent": "Parent level rank must be this unit's rank − 1."}
                    )
            elif geo_level.rank != 0:
                raise serializers.ValidationError(
                    {"parent": "Only top-level (rank 0) units may have no parent."}
                )
        return attrs


class GeoUnitTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = GeoUnit
        fields = ["id", "name", "code", "geo_level", "population", "is_active", "children"]

    def get_children(self, obj):
        return GeoUnitTreeSerializer(obj.children.all(), many=True).data
