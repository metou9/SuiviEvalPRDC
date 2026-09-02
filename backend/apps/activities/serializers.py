from rest_framework import serializers

from .models import (
    Activity,
    ActivityParticipant,
    TechnicalExecution,
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

    # ------------------------------------------------------------------
    # VALIDATION EXERCICE
    # ------------------------------------------------------------------

    def validate_year(self, value):
        if value < 2010 or value > 2090:
            raise serializers.ValidationError(
                "L'exercice doit être compris entre 2010 et 2090."
            )

        return value

    # ------------------------------------------------------------------
    # VALIDATION GENERALE
    # ------------------------------------------------------------------

    def validate(self, attrs):
        instance = self.instance

        start_date = attrs.get(
            "start_date",
            getattr(instance, "start_date", None),
        )

        end_date = attrs.get(
            "end_date",
            getattr(instance, "end_date", None),
        )

        if (
            start_date
            and end_date
            and end_date < start_date
        ):
            raise serializers.ValidationError({
                "end_date":
                    "La date de fin ne peut pas être "
                    "antérieure à la date de début."
            })

        return attrs


# ======================================================================
# ACTIVITE
# ======================================================================

class ActivitySerializer(serializers.ModelSerializer):

    # ------------------------------------------------------------------
    # CODE / INTITULE
    #
    # Ce sont les SEULS champs obligatoires pour créer une activité.
    # ------------------------------------------------------------------

    code = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False,
    )

    title = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False,
    )

    # ------------------------------------------------------------------
    # PARTICIPANTS
    # ------------------------------------------------------------------

    participants = ActivityParticipantSerializer(
        many=True,
        required=False,
    )

    # ------------------------------------------------------------------
    # SOUS-COMPOSANTE
    # ------------------------------------------------------------------

    program_node_code = serializers.CharField(
        source="program_node.code",
        read_only=True,
    )

    program_node_name = serializers.CharField(
        source="program_node.name",
        read_only=True,
    )

    # ------------------------------------------------------------------
    # COMPOSANTE DEDUITE
    # ------------------------------------------------------------------

    component_code = serializers.CharField(
        source="program_node.parent.code",
        read_only=True,
    )

    component_name = serializers.CharField(
        source="program_node.parent.name",
        read_only=True,
    )

    # ------------------------------------------------------------------
    # ZONE D'INTERVENTION
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
    # RESPONSABLE / PARTENAIRE
    # ------------------------------------------------------------------

    responsible_name = serializers.CharField(
        source="responsible.name",
        read_only=True,
    )

    # ------------------------------------------------------------------
    # UNITE DE MESURE
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
    # INDICATEUR
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

        # --------------------------------------------------------------
        # SEULS CODE + INTITULE SONT OBLIGATOIRES
        # --------------------------------------------------------------

        extra_kwargs = {
            "program_node": {
                "required": False,
                "allow_null": True,
            },

            "geo_unit": {
                "required": False,
                "allow_null": True,
            },

            "responsible": {
                "required": False,
                "allow_null": True,
            },

            "unit": {
                "required": False,
                "allow_null": True,
            },

            "indicator": {
                "required": False,
                "allow_null": True,
            },

            "objective": {
                "required": False,
                "allow_blank": True,
            },

            "description": {
                "required": False,
                "allow_blank": True,
            },
        }

    # ==================================================================
    # VALIDATION
    # ==================================================================

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
        # SOUS-COMPOSANTE
        #
        # FACULTATIVE.
        # Si elle est renseignée, elle doit réellement être
        # une sous-composante du projet courant.
        # ----------------------------------------------------------

        if (
            program_node
            and program_node.node_type
            != ProgramNode.NodeType.SUBCOMPONENT
        ):
            raise serializers.ValidationError({
                "program_node":
                    "L'activité doit être rattachée à une sous-composante."
            })

        if (
            program_node
            and project
            and program_node.project_id != project.id
        ):
            raise serializers.ValidationError({
                "program_node":
                    "La sous-composante doit appartenir au projet courant."
            })

        # ----------------------------------------------------------
        # ZONE
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
        # RESPONSABLE
        # ----------------------------------------------------------

        if (
            responsible
            and project
            and responsible.project_id != project.id
        ):
            raise serializers.ValidationError({
                "responsible":
                    "Le responsable/partenaire doit appartenir "
                    "au projet courant."
            })

        # ----------------------------------------------------------
        # UNITE
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
        # INDICATEUR
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
        # COHERENCE INDICATEUR / SOUS-COMPOSANTE
        #
        # Cette vérification n'est effectuée que lorsque les deux
        # informations sont renseignées.
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

    # ------------------------------------------------------------------
    # PARTICIPANTS
    # ------------------------------------------------------------------

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
    # EXERCICE
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
    # ACTIVITE
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
    # SOUS-COMPOSANTE / COMPOSANTE
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
    # UNITE
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
    # ZONE
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
    # RESPONSABLE
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

            # Exercice
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

            # Dates prévues
            "planned_start_date",
            "planned_end_date",

            # Programmation
            "implementation_modality",
            "expected_output",
            "observations",

            # Chronogramme
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
        # EXERCICE OBLIGATOIRE
        # ----------------------------------------------------------

        if workplan is None:
            raise serializers.ValidationError({
                "workplan":
                    "L'exercice est obligatoire."
            })

        if (
            project
            and workplan.project_id != project.id
        ):
            raise serializers.ValidationError({
                "workplan":
                    "L'exercice doit appartenir au projet courant."
            })

        if (
            workplan.year < 2010
            or workplan.year > 2090
        ):
            raise serializers.ValidationError({
                "workplan":
                    "L'exercice doit être compris entre 2010 et 2090."
            })

        # ----------------------------------------------------------
        # ACTIVITE OBLIGATOIRE
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
        # UNITE
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
        # ZONE
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
        # RESPONSABLE
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
        # DATES
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
    # ENREGISTREMENT DU CHRONOGRAMME
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


# ======================================================================
# EXECUTION / SUIVI TECHNIQUE
# ======================================================================

class TechnicalExecutionSerializer(serializers.ModelSerializer):

    # ------------------------------------------------------------------
    # ACTIVITE
    # ------------------------------------------------------------------

    activity_id = serializers.IntegerField(
        source="technical_plan.activity.id",
        read_only=True,
    )

    activity_code = serializers.CharField(
        source="technical_plan.activity.code",
        read_only=True,
        allow_null=True,
    )

    activity_title = serializers.CharField(
        source="technical_plan.activity.title",
        read_only=True,
    )

    # ------------------------------------------------------------------
    # EXERCICE
    # ------------------------------------------------------------------

    workplan_id = serializers.IntegerField(
        source="technical_plan.workplan.id",
        read_only=True,
    )

    workplan_year = serializers.IntegerField(
        source="technical_plan.workplan.year",
        read_only=True,
    )

    # ------------------------------------------------------------------
    # PROGRAMMATION PREVUE
    # ------------------------------------------------------------------

    planned_quantity = serializers.DecimalField(
        source="technical_plan.planned_quantity",
        max_digits=18,
        decimal_places=2,
        read_only=True,
        allow_null=True,
    )

    planned_start_date = serializers.DateField(
        source="technical_plan.planned_start_date",
        read_only=True,
        allow_null=True,
    )

    planned_end_date = serializers.DateField(
        source="technical_plan.planned_end_date",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # UNITE
    # ------------------------------------------------------------------

    unit_name = serializers.CharField(
        source="technical_plan.unit.name",
        read_only=True,
        allow_null=True,
    )

    unit_symbol = serializers.CharField(
        source="technical_plan.unit.symbol",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # RESPONSABLE
    # ------------------------------------------------------------------

    responsible_name = serializers.CharField(
        source="technical_plan.responsible.name",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # SOUS-COMPOSANTE
    # ------------------------------------------------------------------

    program_node_name = serializers.CharField(
        source="technical_plan.activity.program_node.name",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # COMPOSANTE
    # ------------------------------------------------------------------

    component_name = serializers.CharField(
        source="technical_plan.activity.program_node.parent.name",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # ZONE
    # ------------------------------------------------------------------

    geo_unit_name = serializers.CharField(
        source="technical_plan.geo_unit.name",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # STATUT
    # ------------------------------------------------------------------

    execution_status_label = serializers.CharField(
        source="get_execution_status_display",
        read_only=True,
    )

    class Meta:
        model = TechnicalExecution

        fields = [
            "id",
            "project",

            # Programmation technique
            "technical_plan",

            # Activité
            "activity_id",
            "activity_code",
            "activity_title",

            # Composante / Sous-composante
            "component_name",
            "program_node_name",

            # Exercice
            "workplan_id",
            "workplan_year",

            # Programmation prévue
            "planned_quantity",
            "planned_start_date",
            "planned_end_date",

            # Unité
            "unit_name",
            "unit_symbol",

            # Zone
            "geo_unit_name",

            # Responsable
            "responsible_name",

            # Date de suivi
            "reporting_date",

            # Période
            "period_year",
            "period_quarter",
            "period_month",

            # Réalisation
            "actual_quantity",
            "physical_progress_percent",
            "execution_status",
            "execution_status_label",

            # Dates réelles
            "actual_start_date",
            "actual_end_date",

            # Difficultés / actions
            "difficulties",
            "corrective_actions",
            "observations",

            # Audit
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]

        read_only_fields = [
            "project",
            "physical_progress_percent",

            "activity_id",
            "activity_code",
            "activity_title",

            "component_name",
            "program_node_name",

            "workplan_id",
            "workplan_year",

            "planned_quantity",
            "planned_start_date",
            "planned_end_date",

            "unit_name",
            "unit_symbol",

            "geo_unit_name",
            "responsible_name",

            "execution_status_label",

            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]

    # ==================================================================
    # VALIDATION
    # ==================================================================

    def validate(self, attrs):
        instance = self.instance

        technical_plan = attrs.get(
            "technical_plan",
            getattr(
                instance,
                "technical_plan",
                None,
            ),
        )

        reporting_date = attrs.get(
            "reporting_date",
            getattr(
                instance,
                "reporting_date",
                None,
            ),
        )

        period_year = attrs.get(
            "period_year",
            getattr(
                instance,
                "period_year",
                None,
            ),
        )

        period_quarter = attrs.get(
            "period_quarter",
            getattr(
                instance,
                "period_quarter",
                None,
            ),
        )

        period_month = attrs.get(
            "period_month",
            getattr(
                instance,
                "period_month",
                None,
            ),
        )

        actual_quantity = attrs.get(
            "actual_quantity",
            getattr(
                instance,
                "actual_quantity",
                None,
            ),
        )

        actual_start_date = attrs.get(
            "actual_start_date",
            getattr(
                instance,
                "actual_start_date",
                None,
            ),
        )

        actual_end_date = attrs.get(
            "actual_end_date",
            getattr(
                instance,
                "actual_end_date",
                None,
            ),
        )

        request = self.context.get("request")
        project = getattr(request, "project", None)

        if (
            not project
            and instance
        ):
            project = instance.project

        # ----------------------------------------------------------
        # PROGRAMMATION TECHNIQUE OBLIGATOIRE
        # ----------------------------------------------------------

        if technical_plan is None:
            raise serializers.ValidationError({
                "technical_plan":
                    "La programmation technique est obligatoire."
            })

        if (
            project
            and technical_plan.project_id != project.id
        ):
            raise serializers.ValidationError({
                "technical_plan":
                    "La programmation technique doit appartenir "
                    "au projet courant."
            })

        # ----------------------------------------------------------
        # EXERCICE
        # ----------------------------------------------------------

        if period_year is None:
            raise serializers.ValidationError({
                "period_year":
                    "L'exercice est obligatoire."
            })

        if (
            period_year < 2010
            or period_year > 2090
        ):
            raise serializers.ValidationError({
                "period_year":
                    "L'exercice doit être compris entre 2010 et 2090."
            })

        if (
            technical_plan
            and technical_plan.workplan_id
            and period_year != technical_plan.workplan.year
        ):
            raise serializers.ValidationError({
                "period_year":
                    "L'exercice du suivi doit correspondre "
                    "à l'exercice de la programmation technique."
            })

        # ----------------------------------------------------------
        # DATE DE SUIVI
        # ----------------------------------------------------------

        if reporting_date is None:
            raise serializers.ValidationError({
                "reporting_date":
                    "La date de suivi est obligatoire."
            })

        # ----------------------------------------------------------
        # TRIMESTRE
        # ----------------------------------------------------------

        if period_quarter is not None:
            if (
                period_quarter < 1
                or period_quarter > 4
            ):
                raise serializers.ValidationError({
                    "period_quarter":
                        "Le trimestre doit être compris entre 1 et 4."
                })

        # ----------------------------------------------------------
        # MOIS
        # ----------------------------------------------------------

        if period_month is not None:
            if (
                period_month < 1
                or period_month > 12
            ):
                raise serializers.ValidationError({
                    "period_month":
                        "Le mois doit être compris entre 1 et 12."
                })

        # ----------------------------------------------------------
        # COHERENCE MOIS / TRIMESTRE
        # ----------------------------------------------------------

        if (
            period_month is not None
            and period_quarter is not None
        ):
            expected_quarter = (
                (period_month - 1) // 3
            ) + 1

            if period_quarter != expected_quarter:
                raise serializers.ValidationError({
                    "period_quarter":
                        "Le trimestre ne correspond pas "
                        "au mois sélectionné."
                })

        # ----------------------------------------------------------
        # QUANTITE REALISEE
        # ----------------------------------------------------------

        if (
            actual_quantity is not None
            and actual_quantity < 0
        ):
            raise serializers.ValidationError({
                "actual_quantity":
                    "La quantité réalisée ne peut pas être négative."
            })

        # ----------------------------------------------------------
        # DATES REELLES
        # ----------------------------------------------------------

        if (
            actual_start_date
            and actual_end_date
            and actual_end_date < actual_start_date
        ):
            raise serializers.ValidationError({
                "actual_end_date":
                    "La date réelle de fin ne peut pas être "
                    "antérieure à la date réelle de début."
            })

        return attrs