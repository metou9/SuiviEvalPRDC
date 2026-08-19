from rest_framework import serializers

from .models import (
    Activity,
    ActivityParticipant,
    TechnicalPlan,
    TechnicalSchedule,
    WorkPlan,
)


# ======================================================================
# PARTICIPANTS
# ======================================================================

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


# ======================================================================
# PTBA / PLAN DE TRAVAIL ANNUEL
# ======================================================================

class WorkPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkPlan

        fields = [
            "id",
            "project",
            "code",
            "name",
            "year",
            "version",
            "start_date",
            "end_date",
            "is_current",
            "is_active",
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


# ======================================================================
# ACTIVITÉ
# ======================================================================

class ActivitySerializer(serializers.ModelSerializer):
    participants = ActivityParticipantSerializer(
        many=True,
        required=False,
    )

    # ------------------------------------------------------------------
    # Sous-composante
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Zone d'intervention
    # ------------------------------------------------------------------

    geo_unit_name = serializers.CharField(
        source="geo_unit.name",
        read_only=True,
    )

    geo_level_name = serializers.CharField(
        source="geo_unit.geo_level.name",
        read_only=True,
    )

    # ------------------------------------------------------------------
    # Responsable / Partenaire
    # ------------------------------------------------------------------

    responsible_name = serializers.CharField(
        source="responsible.name",
        read_only=True,
    )

    # ------------------------------------------------------------------
    # Unité de mesure
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Indicateur
    # ------------------------------------------------------------------

    indicator_code = serializers.CharField(
        source="indicator.code",
        read_only=True,
    )

    indicator_name = serializers.CharField(
        source="indicator.name",
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

            # Sous-composante
            "program_node",
            "program_node_code",
            "program_node_name",

            # Composante déduite
            "component_code",
            "component_name",

            # Zone d'intervention
            "geo_unit",
            "geo_unit_name",
            "geo_level_name",

            # Responsable / Partenaire
            "responsible",
            "responsible_name",

            # Unité de mesure
            "unit",
            "unit_code",
            "unit_name",
            "unit_symbol",

            # Indicateur
            "indicator",
            "indicator_code",
            "indicator_name",

            # Informations générales
            "objective",
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

        geo_unit = attrs.get(
            "geo_unit",
            getattr(instance, "geo_unit", None),
        )

        responsible = attrs.get(
            "responsible",
            getattr(instance, "responsible", None),
        )

        unit = attrs.get(
            "unit",
            getattr(instance, "unit", None),
        )

        indicator = attrs.get(
            "indicator",
            getattr(instance, "indicator", None),
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

        if (
            program_node.node_type
            != ProgramNode.NodeType.SUBCOMPONENT
        ):
            raise serializers.ValidationError({
                "program_node":
                "L'activité doit être rattachée à une sous-composante."
            })

        if (
            project
            and program_node.project_id != project.id
        ):
            raise serializers.ValidationError({
                "program_node":
                "La sous-composante doit appartenir au projet courant."
            })

        # ----------------------------------------------------------
        # Zone d'intervention
        # ----------------------------------------------------------

        if (
            geo_unit
            and project
            and geo_unit.project_id != project.id
        ):
            raise serializers.ValidationError({
                "geo_unit":
                "La zone d'intervention doit appartenir au projet courant."
            })

        # ----------------------------------------------------------
        # Responsable / Partenaire
        # ----------------------------------------------------------

        if (
            responsible
            and project
            and responsible.project_id != project.id
        ):
            raise serializers.ValidationError({
                "responsible":
                "Le responsable/partenaire doit appartenir au projet courant."
            })

        # ----------------------------------------------------------
        # Unité de mesure
        # ----------------------------------------------------------

        if (
            unit
            and project
            and unit.project_id != project.id
        ):
            raise serializers.ValidationError({
                "unit":
                "L'unité de mesure doit appartenir au projet courant."
            })

        # ----------------------------------------------------------
        # Indicateur
        # ----------------------------------------------------------

        if (
            indicator
            and project
            and indicator.project_id != project.id
        ):
            raise serializers.ValidationError({
                "indicator":
                "L'indicateur doit appartenir au projet courant."
            })

        # ----------------------------------------------------------
        # Cohérence indicateur / sous-composante
        # ----------------------------------------------------------

        if (
            indicator
            and program_node
            and indicator.program_node_id
        ):
            allowed_ids = {
                program_node.id,
            }

            frontier = [
                program_node.id,
            ]

            while frontier:
                children = list(
                    ProgramNode.objects.filter(
                        parent_id__in=frontier
                    ).values_list(
                        "id",
                        flat=True,
                    )
                )

                children = [
                    child_id
                    for child_id in children
                    if child_id not in allowed_ids
                ]

                allowed_ids.update(
                    children
                )

                frontier = children

            if indicator.program_node_id not in allowed_ids:
                raise serializers.ValidationError({
                    "indicator":
                    "Cet indicateur n'appartient pas à la "
                    "sous-composante sélectionnée."
                })

        return attrs

    def _save_participants(
        self,
        activity,
        participants,
    ):
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

    def update(
        self,
        instance,
        validated_data,
    ):
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


# ======================================================================
# CALENDRIER MENSUEL PTBA
# ======================================================================

class TechnicalScheduleSerializer(serializers.ModelSerializer):
    month_label = serializers.CharField(
        source="get_month_display",
        read_only=True,
    )

    class Meta:
        model = TechnicalSchedule

        fields = [
            "id",
            "project",
            "technical_plan",
            "month",
            "month_label",
            "is_planned",
            "planned_quantity",
            "note",
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


# ======================================================================
# PROGRAMMATION TECHNIQUE PTBA
# ======================================================================

class TechnicalPlanSerializer(serializers.ModelSerializer):
    schedule = TechnicalScheduleSerializer(
        many=True,
        required=False,
    )

    # ------------------------------------------------------------------
    # PTBA
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Activité
    # ------------------------------------------------------------------

    activity_code = serializers.CharField(
        source="activity.code",
        read_only=True,
    )

    activity_title = serializers.CharField(
        source="activity.title",
        read_only=True,
    )

    # ------------------------------------------------------------------
    # Sous-composante de l'activité
    # ------------------------------------------------------------------

    program_node_code = serializers.CharField(
        source="activity.program_node.code",
        read_only=True,
    )

    program_node_name = serializers.CharField(
        source="activity.program_node.name",
        read_only=True,
    )

    component_code = serializers.CharField(
        source="activity.program_node.parent.code",
        read_only=True,
    )

    component_name = serializers.CharField(
        source="activity.program_node.parent.name",
        read_only=True,
    )

    # ------------------------------------------------------------------
    # Unité
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Zone
    # ------------------------------------------------------------------

    geo_unit_name = serializers.CharField(
        source="geo_unit.name",
        read_only=True,
    )

    geo_level_name = serializers.CharField(
        source="geo_unit.geo_level.name",
        read_only=True,
    )

    # ------------------------------------------------------------------
    # Responsable
    # ------------------------------------------------------------------

    responsible_name = serializers.CharField(
        source="responsible.name",
        read_only=True,
    )

    class Meta:
        model = TechnicalPlan

        fields = [
            "id",
            "project",

            # PTBA
            "workplan",
            "workplan_code",
            "workplan_name",
            "workplan_year",

            # Activité
            "activity",
            "activity_code",
            "activity_title",

            # Composante / Sous-composante
            "program_node_code",
            "program_node_name",
            "component_code",
            "component_name",

            # Quantité prévue
            "planned_quantity",

            # Unité
            "unit",
            "unit_code",
            "unit_name",
            "unit_symbol",

            # Zone
            "geo_unit",
            "geo_unit_name",
            "geo_level_name",

            # Responsable
            "responsible",
            "responsible_name",

            # Période prévue
            "planned_start_date",
            "planned_end_date",

            # PTBA
            "implementation_modality",
            "expected_output",
            "observations",

            # Chronogramme mensuel
            "schedule",

            # Audit
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
        instance = self.instance

        workplan = attrs.get(
            "workplan",
            getattr(instance, "workplan", None),
        )

        activity = attrs.get(
            "activity",
            getattr(instance, "activity", None),
        )

        unit = attrs.get(
            "unit",
            getattr(instance, "unit", None),
        )

        geo_unit = attrs.get(
            "geo_unit",
            getattr(instance, "geo_unit", None),
        )

        responsible = attrs.get(
            "responsible",
            getattr(instance, "responsible", None),
        )

        planned_start_date = attrs.get(
            "planned_start_date",
            getattr(instance, "planned_start_date", None),
        )

        planned_end_date = attrs.get(
            "planned_end_date",
            getattr(instance, "planned_end_date", None),
        )

        request = self.context.get("request")
        project = getattr(request, "project", None)

        # ----------------------------------------------------------
        # PTBA obligatoire
        # ----------------------------------------------------------

        if workplan is None:
            raise serializers.ValidationError({
                "workplan":
                "Le PTBA est obligatoire."
            })

        if (
            project
            and workplan.project_id != project.id
        ):
            raise serializers.ValidationError({
                "workplan":
                "Le PTBA doit appartenir au projet courant."
            })

        # ----------------------------------------------------------
        # Activité obligatoire
        # ----------------------------------------------------------

        if activity is None:
            raise serializers.ValidationError({
                "activity":
                "L'activité est obligatoire."
            })

        if (
            project
            and activity.project_id != project.id
        ):
            raise serializers.ValidationError({
                "activity":
                "L'activité doit appartenir au projet courant."
            })

        # ----------------------------------------------------------
        # Unité
        # ----------------------------------------------------------

        if (
            unit
            and project
            and unit.project_id != project.id
        ):
            raise serializers.ValidationError({
                "unit":
                "L'unité de mesure doit appartenir au projet courant."
            })

        # ----------------------------------------------------------
        # Zone
        # ----------------------------------------------------------

        if (
            geo_unit
            and project
            and geo_unit.project_id != project.id
        ):
            raise serializers.ValidationError({
                "geo_unit":
                "La zone d'intervention doit appartenir au projet courant."
            })

        # ----------------------------------------------------------
        # Responsable
        # ----------------------------------------------------------

        if (
            responsible
            and project
            and responsible.project_id != project.id
        ):
            raise serializers.ValidationError({
                "responsible":
                "Le responsable doit appartenir au projet courant."
            })

        # ----------------------------------------------------------
        # Dates
        # ----------------------------------------------------------

        if (
            planned_start_date
            and planned_end_date
            and planned_end_date < planned_start_date
        ):
            raise serializers.ValidationError({
                "planned_end_date":
                "La date prévue de fin ne peut pas être "
                "antérieure à la date prévue de début."
            })

        return attrs

    # ------------------------------------------------------------------
    # Enregistrement du chronogramme
    # ------------------------------------------------------------------

    def _save_schedule(
        self,
        technical_plan,
        schedule_data,
    ):
        technical_plan.schedule.all().delete()

        for item in schedule_data:
            TechnicalSchedule.objects.create(
                project=technical_plan.project,
                technical_plan=technical_plan,
                **item,
            )

    def create(self, validated_data):
        schedule_data = validated_data.pop(
            "schedule",
            [],
        )

        technical_plan = super().create(
            validated_data
        )

        self._save_schedule(
            technical_plan,
            schedule_data,
        )

        return technical_plan

    def update(
        self,
        instance,
        validated_data,
    ):
        schedule_data = validated_data.pop(
            "schedule",
            None,
        )

        technical_plan = super().update(
            instance,
            validated_data,
        )

        if schedule_data is not None:
            self._save_schedule(
                technical_plan,
                schedule_data,
            )

        return technical_plan