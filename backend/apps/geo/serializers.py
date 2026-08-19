from rest_framework import serializers

from .models import GeoLevel, GeoUnit


class GeoLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoLevel
        fields = [
            "id",
            "project",
            "name",
            "name_plural",
            "rank",
            "code",
        ]
        read_only_fields = ["project"]


class GeoUnitSerializer(serializers.ModelSerializer):
    geo_level_rank = serializers.IntegerField(
        source="geo_level.rank",
        read_only=True,
    )

    geo_level_name = serializers.CharField(
        source="geo_level.name",
        read_only=True,
    )

    parent_name = serializers.CharField(
        source="parent.name",
        read_only=True,
    )

    parent_level_name = serializers.CharField(
        source="parent.geo_level.name",
        read_only=True,
    )

    class Meta:
        model = GeoUnit
        fields = [
            "id",
            "project",

            "geo_level",
            "geo_level_rank",
            "geo_level_name",

            "parent",
            "parent_name",
            "parent_level_name",

            "name",
            "code",

            "population",
            "latitude",
            "longitude",
            "geojson",

            "is_active",
        ]

        read_only_fields = ["project"]

    def validate(self, attrs):
        """
        Validation de la hiérarchie géographique.

        Structure générique conservée.

        Pour PRDC-VFS :

        Pays
          └── Wilaya
                └── Moughataa
                      └── Commune
                            └── Village / Localité
        """

        instance = self.instance

        geo_level = attrs.get(
            "geo_level",
            getattr(instance, "geo_level", None),
        )

        parent = attrs.get(
            "parent",
            getattr(instance, "parent", None),
        )

        # Le projet est fourni par AuthoredModelViewSet
        # lors de la création.
        request = self.context.get("request")
        request_project = getattr(
            request,
            "project",
            None,
        )

        # ---------------------------------------------------------
        # Vérifier que le niveau appartient au projet courant
        # ---------------------------------------------------------

        if (
            request_project is not None
            and geo_level is not None
            and geo_level.project_id != request_project.id
        ):
            raise serializers.ValidationError(
                {
                    "geo_level":
                    "Le niveau géographique doit appartenir au projet courant."
                }
            )

        # ---------------------------------------------------------
        # Validation du parent
        # ---------------------------------------------------------

        if parent is not None:

            # Une unité ne peut pas être son propre parent.
            if (
                instance is not None
                and parent.id == instance.id
            ):
                raise serializers.ValidationError(
                    {
                        "parent":
                        "Une unité géographique ne peut pas être son propre parent."
                    }
                )

            # Le parent doit appartenir au projet courant.
            if (
                request_project is not None
                and parent.project_id != request_project.id
            ):
                raise serializers.ValidationError(
                    {
                        "parent":
                        "Le parent doit appartenir au même projet."
                    }
                )

            # Le parent doit être exactement un niveau au-dessus.
            if (
                geo_level is not None
                and parent.geo_level.rank
                != geo_level.rank - 1
            ):
                raise serializers.ValidationError(
                    {
                        "parent":
                        "Le parent doit appartenir au niveau géographique immédiatement supérieur."
                    }
                )

        # ---------------------------------------------------------
        # Une unité sans parent est autorisée uniquement au rang 0
        # ---------------------------------------------------------

        elif (
            geo_level is not None
            and geo_level.rank != 0
        ):
            raise serializers.ValidationError(
                {
                    "parent":
                    "Seules les unités du niveau géographique supérieur peuvent ne pas avoir de parent."
                }
            )

        return attrs


class GeoUnitTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    geo_level_name = serializers.CharField(
        source="geo_level.name",
        read_only=True,
    )

    geo_level_rank = serializers.IntegerField(
        source="geo_level.rank",
        read_only=True,
    )

    class Meta:
        model = GeoUnit
        fields = [
            "id",
            "name",
            "code",

            "geo_level",
            "geo_level_name",
            "geo_level_rank",

            "population",
            "latitude",
            "longitude",

            "is_active",

            "children",
        ]

    def get_children(self, obj):
        return GeoUnitTreeSerializer(
            obj.children
            .select_related("geo_level")
            .all()
            .order_by(
                "geo_level__rank",
                "name",
            ),
            many=True,
            context=self.context,
        ).data