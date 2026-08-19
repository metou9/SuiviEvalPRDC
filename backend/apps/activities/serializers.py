from rest_framework import serializers

from .models import Activity, ActivityParticipant


class ActivityParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityParticipant
        fields = [
            "id",
            "full_name",
            "origin",
            "organization",
            "function",
            "sex",
        ]


class ActivitySerializer(serializers.ModelSerializer):
    participants = ActivityParticipantSerializer(
        many=True,
        required=False,
    )

    # --------------------------------------------------------------
    # PTBA / Exercice
    # --------------------------------------------------------------

    workplan_code = serializers.CharField(
        source="workplan.code",
        read_only=True,
    )

    workplan_name = serializers.CharField(
        source="workplan.name",
        read_only=True,
    )

    workplan_year = serializers.IntegerField(
        source="workplan.year",
        read_only=True,
    )

    # --------------------------------------------------------------
    # Sous-composante
    # --------------------------------------------------------------

    program_node_code = serializers.CharField(
        source="program_node.code",
        read_only=True,
    )

    program_node_name = serializers.CharField(
        source="program_node.name",
        read_only=True,
    )

    # Composante obtenue automatiquement via la sous-composante
    component_code = serializers.CharField(
        source="program_node.parent.code",
        read_only=True,
    )

    component_name = serializers.CharField(
        source="program_node.parent.name",
        read_only=True,
    )

    # --------------------------------------------------------------
    # Responsable / Partenaire
    # --------------------------------------------------------------

    responsible_name = serializers.CharField(
        source="responsible.name",
        read_only=True,
    )

    # --------------------------------------------------------------
    # Unité de mesure
    # --------------------------------------------------------------

    unit_code = serializers.CharField(
        source="unit.code",
        read_only=True,
    )

    unit_name = serializers.CharField(
        source="unit.name",
        read_only=True,
    )

    unit_symbol = serializers.CharField(
        source="unit.symbol",
        read_only=True,
    )

    class Meta:
        model = Activity

        fields = [
            "id",
            "project",

            # Référence activité
            "code",
            "title",

            # PTBA / Exercice
            "workplan",
            "workplan_code",
            "workplan_name",
            "workplan_year",

            # Sous-composante
            "program_node",
            "program_node_code",
            "program_node_name",

            # Composante déduite
            "component_code",
            "component_name",

            # Responsable / Partenaire
            "responsible",
            "responsible_name",

            # Dates
            "start_date",
            "end_date",

            # Unité / quantité
            "unit",
            "unit_code",
            "unit_name",
            "unit_symbol",
            "planned_quantity",

            # Importance
            "importance",

            # Budget programmé
            "programmed_budget",

            # Description
            "description",

            # Participants
            "participants",

            # Audit automatique
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]

        read_only_fields = [
            "project",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]

    def validate(self, attrs):
        from apps.program.models import ProgramNode

        instance = self.instance

        program_node = attrs.get(
            "program_node",
            getattr(instance, "program_node", None),
        )

        workplan = attrs.get(
            "workplan",
            getattr(instance, "workplan", None),
        )

        responsible = attrs.get(
            "responsible",
            getattr(instance, "responsible", None),
        )

        unit = attrs.get(
            "unit",
            getattr(instance, "unit", None),
        )

        start_date = attrs.get(
            "start_date",
            getattr(instance, "start_date", None),
        )

        end_date = attrs.get(
            "end_date",
            getattr(instance, "end_date", None),
        )

        request = self.context.get("request")
        project = getattr(request, "project", None)

        # ----------------------------------------------------------
        # Sous-composante obligatoire
        # ----------------------------------------------------------

        if program_node is None:
            raise serializers.ValidationError({
                "program_node":
                "La sous-composante est obligatoire."
            })

        if program_node.node_type != ProgramNode.NodeType.SUBCOMPONENT:
            raise serializers.ValidationError({
                "program_node":
                "L'activité doit être rattachée à une sous-composante."
            })

        if project and program_node.project_id != project.id:
            raise serializers.ValidationError({
                "program_node":
                "La sous-composante doit appartenir au projet courant."
            })

        # ----------------------------------------------------------
        # PTBA / Exercice
        # ----------------------------------------------------------

        if workplan and project and workplan.project_id != project.id:
            raise serializers.ValidationError({
                "workplan":
                "Le PTBA doit appartenir au projet courant."
            })

        # ----------------------------------------------------------
        # Responsable / Partenaire
        # ----------------------------------------------------------

        if responsible and project and responsible.project_id != project.id:
            raise serializers.ValidationError({
                "responsible":
                "Le responsable/partenaire doit appartenir au projet courant."
            })

        # ----------------------------------------------------------
        # Unité de mesure
        # ----------------------------------------------------------

        if unit and project and unit.project_id != project.id:
            raise serializers.ValidationError({
                "unit":
                "L'unité de mesure doit appartenir au projet courant."
            })

        # ----------------------------------------------------------
        # Dates
        # ----------------------------------------------------------

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({
                "end_date":
                "La date de fin ne peut pas être antérieure à la date de début."
            })

        return attrs

    def _save_participants(self, activity, participants):
        activity.participants.all().delete()

        for item in participants:
            ActivityParticipant.objects.create(
                activity=activity,
                **item,
            )

    def create(self, validated_data):
        participants = validated_data.pop(
            "participants",
            [],
        )

        activity = super().create(
            validated_data
        )

        self._save_participants(
            activity,
            participants,
        )

        return activity

    def update(self, instance, validated_data):
        participants = validated_data.pop(
            "participants",
            None,
        )

        activity = super().update(
            instance,
            validated_data,
        )

        if participants is not None:
            self._save_participants(
                activity,
                participants,
            )

        return activity