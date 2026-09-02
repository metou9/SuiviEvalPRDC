from rest_framework import serializers

from .models import (
    PPMItem,
    ProcurementMethod,
    ProcurementProcess,
    ProcurementStage,
    StageEvent,
)


# ======================================================================
# METHODES DE PASSATION
# ======================================================================

class ProcurementMethodSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProcurementMethod

        fields = [
            "id",
            "project",
            "parent",
            "code",
            "name",
            "order",
            "is_active",
        ]

        read_only_fields = [
            "project",
        ]


# ======================================================================
# ETAPES DE PASSATION
# ======================================================================

class ProcurementStageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProcurementStage

        fields = [
            "id",
            "project",
            "code",
            "name",
            "order",
        ]

        read_only_fields = [
            "project",
        ]


# ======================================================================
# PROGRAMMATION DES MARCHES
# ======================================================================

class PPMItemSerializer(serializers.ModelSerializer):

    # ------------------------------------------------------------------
    # AFFICHAGE ACTIVITE
    # ------------------------------------------------------------------

    activity_code = serializers.CharField(
        source="activity.code",
        read_only=True,
        allow_null=True,
    )

    activity_title = serializers.CharField(
        source="activity.title",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # AFFICHAGE SOUS-COMPOSANTE
    # ------------------------------------------------------------------

    program_node_name = serializers.CharField(
        source="program_node.name",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # AFFICHAGE CATEGORIE DE DEPENSE
    # ------------------------------------------------------------------

    expense_category_name = serializers.CharField(
        source="expense_category.name",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # AFFICHAGE METHODE DE PASSATION
    # ------------------------------------------------------------------

    procurement_method_name = serializers.CharField(
        source="procurement_method.name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = PPMItem

        fields = [
            "id",
            "project",

            # Référence
            "ppm_ref",

            # Activité facultative
            "activity",
            "activity_code",
            "activity_title",

            # Intitulé du marché
            "designation",

            # Sous-composante
            "program_node",
            "program_node_name",

            # Catégorie de dépense
            "expense_category",
            "expense_category_name",

            # Méthode de passation
            "procurement_method",
            "procurement_method_name",

            # Coût estimatif
            "planned_amount",

            # Exercice
            "planned_year",

            # Dates prévues
            "planned_contract_signature_date",
            "planned_contract_end_date",

            # Etat
            "is_active",
        ]

        read_only_fields = [
            "project",
            "activity_code",
            "activity_title",
            "program_node_name",
            "expense_category_name",
            "procurement_method_name",
        ]

    # ==================================================================
    # VALIDATION
    # ==================================================================

    def validate(self, attrs):

        instance = getattr(
            self,
            "instance",
            None,
        )

        # --------------------------------------------------------------
        # PROJET COURANT
        # --------------------------------------------------------------

        project = None

        request = self.context.get(
            "request"
        )

        if request:
            project = getattr(
                request,
                "project",
                None,
            )

        if not project and instance:
            project = instance.project

        # --------------------------------------------------------------
        # VALEURS FINALES
        # --------------------------------------------------------------

        activity = attrs.get(
            "activity",
            getattr(
                instance,
                "activity",
                None,
            ),
        )

        program_node = attrs.get(
            "program_node",
            getattr(
                instance,
                "program_node",
                None,
            ),
        )

        expense_category = attrs.get(
            "expense_category",
            getattr(
                instance,
                "expense_category",
                None,
            ),
        )

        procurement_method = attrs.get(
            "procurement_method",
            getattr(
                instance,
                "procurement_method",
                None,
            ),
        )

        planned_year = attrs.get(
            "planned_year",
            getattr(
                instance,
                "planned_year",
                None,
            ),
        )

        planned_contract_signature_date = attrs.get(
            "planned_contract_signature_date",
            getattr(
                instance,
                "planned_contract_signature_date",
                None,
            ),
        )

        planned_contract_end_date = attrs.get(
            "planned_contract_end_date",
            getattr(
                instance,
                "planned_contract_end_date",
                None,
            ),
        )

        # --------------------------------------------------------------
        # ACTIVITE
        #
        # Facultative.
        # --------------------------------------------------------------

        if activity and project:
            if activity.project_id != project.id:
                raise serializers.ValidationError({
                    "activity":
                        "L'activité doit appartenir au projet courant."
                })

        # --------------------------------------------------------------
        # SOUS-COMPOSANTE
        # --------------------------------------------------------------

        if program_node and project:
            if program_node.project_id != project.id:
                raise serializers.ValidationError({
                    "program_node":
                        "La sous-composante doit appartenir "
                        "au projet courant."
                })

        # --------------------------------------------------------------
        # COHERENCE ACTIVITE / SOUS-COMPOSANTE
        # --------------------------------------------------------------

        if activity and program_node:
            if (
                activity.program_node_id
                and
                activity.program_node_id != program_node.id
            ):
                raise serializers.ValidationError({
                    "program_node":
                        "La sous-composante doit correspondre "
                        "à celle de l'activité sélectionnée."
                })

        # --------------------------------------------------------------
        # CATEGORIE DE DEPENSE
        # --------------------------------------------------------------

        if expense_category and project:
            if expense_category.project_id != project.id:
                raise serializers.ValidationError({
                    "expense_category":
                        "La catégorie de dépense doit appartenir "
                        "au projet courant."
                })

        # --------------------------------------------------------------
        # METHODE DE PASSATION
        # --------------------------------------------------------------

        if procurement_method and project:
            if procurement_method.project_id != project.id:
                raise serializers.ValidationError({
                    "procurement_method":
                        "La méthode de passation doit appartenir "
                        "au projet courant."
                })

        # --------------------------------------------------------------
        # EXERCICE
        # --------------------------------------------------------------

        if planned_year is not None:
            if (
                planned_year < 2010
                or
                planned_year > 2090
            ):
                raise serializers.ValidationError({
                    "planned_year":
                        "L'exercice doit être compris entre 2010 et 2090."
                })

        # --------------------------------------------------------------
        # DATES PREVUES DU CONTRAT
        # --------------------------------------------------------------

        if (
            planned_contract_signature_date
            and
            planned_contract_end_date
            and
            planned_contract_end_date
            <
            planned_contract_signature_date
        ):
            raise serializers.ValidationError({
                "planned_contract_end_date":
                    "La date prévue de fin du contrat doit être "
                    "postérieure ou égale à la date prévue "
                    "de signature du contrat."
            })

        return attrs


# ======================================================================
# EVENEMENTS / ETAPES
# ======================================================================

class StageEventSerializer(serializers.ModelSerializer):

    duration_days = serializers.IntegerField(
        read_only=True
    )

    stage_name = serializers.CharField(
        source="procurement_stage.name",
        read_only=True,
    )

    stage_order = serializers.IntegerField(
        source="procurement_stage.order",
        read_only=True,
    )

    class Meta:
        model = StageEvent

        fields = [
            "id",
            "procurement_process",
            "procurement_stage",
            "stage_name",
            "stage_order",
            "start_date",
            "end_date",
            "decision",
            "deadline",
            "duration_days",
        ]


# ======================================================================
# EXECUTION / SUIVI DES MARCHES
# ======================================================================

class ProcurementProcessSerializer(serializers.ModelSerializer):

    stage_events = StageEventSerializer(
        many=True,
        read_only=True,
    )

    current_stage_name = serializers.CharField(
        source="current_stage.name",
        read_only=True,
    )

    class Meta:
        model = ProcurementProcess

        fields = [
            "id",
            "project",
            "ppm_item",
            "designation",
            "procurement_method",
            "expense_category",
            "program_node",
            "geo_unit",
            "estimated_amount",
            "awarded_amount",
            "supplier",
            "current_stage",
            "current_stage_name",
            "is_completed",
            "status",
            "stage_events",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "project",
            "status",
            "created_at",
            "updated_at",
        ]