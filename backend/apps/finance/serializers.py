from rest_framework import serializers

from apps.activities.models import Activity

from .models import (
    BudgetLine,
    ExpenseCategory,
    FinancialTransaction,
    FundingSource,
)


# ======================================================================
# CATEGORIES DE DEPENSES
# ======================================================================

class ExpenseCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ExpenseCategory

        fields = [
            "id",
            "project",
            "code",
            "name",
            "order",
            "is_active",
        ]

        read_only_fields = [
            "project",
        ]


# ======================================================================
# SOURCES DE FINANCEMENT
# ======================================================================

class FundingSourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = FundingSource

        fields = [
            "id",
            "project",
            "code",
            "name",
            "is_active",
        ]

        read_only_fields = [
            "project",
        ]


# ======================================================================
# PROGRAMMATION FINANCIERE / LIGNES BUDGETAIRES
# ======================================================================

class BudgetLineSerializer(serializers.ModelSerializer):

    # ------------------------------------------------------------------
    # ACTIVITE
    # ------------------------------------------------------------------

    activity = serializers.PrimaryKeyRelatedField(
        queryset=Activity.objects.all(),
        required=True,
        allow_null=False,
    )

    # ------------------------------------------------------------------
    # INFORMATIONS D'AFFICHAGE DE L'ACTIVITE
    # ------------------------------------------------------------------

    activity_code = serializers.CharField(
        source="activity.code",
        read_only=True,
        allow_null=True,
    )

    activity_title = serializers.CharField(
        source="activity.title",
        read_only=True,
    )

    # ------------------------------------------------------------------
    # SOUS-COMPOSANTE
    # ------------------------------------------------------------------

    program_node_name = serializers.CharField(
        source="program_node.name",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # COMPOSANTE
    #
    # La ligne budgétaire reste liée à la sous-composante.
    # La composante est obtenue depuis le parent.
    # ------------------------------------------------------------------

    component_id = serializers.IntegerField(
        source="program_node.parent_id",
        read_only=True,
        allow_null=True,
    )

    component_name = serializers.CharField(
        source="program_node.parent.name",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # CATEGORIE DE DEPENSE
    # ------------------------------------------------------------------

    expense_category_name = serializers.CharField(
        source="expense_category.name",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # SOURCE DE FINANCEMENT
    # ------------------------------------------------------------------

    funding_source_name = serializers.CharField(
        source="funding_source.name",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = BudgetLine

        fields = [
            "id",
            "project",

            # Activité
            "activity",
            "activity_code",
            "activity_title",

            # Composante / sous-composante
            "component_id",
            "component_name",
            "program_node",
            "program_node_name",

            # Catégorie
            "expense_category",
            "expense_category_name",

            # Source
            "funding_source",
            "funding_source_name",

            # Programmation
            "fiscal_year",
            "amount",
            "note",
        ]

        read_only_fields = [
            "project",
            "activity_code",
            "activity_title",
            "component_id",
            "component_name",
            "program_node_name",
            "expense_category_name",
            "funding_source_name",
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

        funding_source = attrs.get(
            "funding_source",
            getattr(
                instance,
                "funding_source",
                None,
            ),
        )

        fiscal_year = attrs.get(
            "fiscal_year",
            getattr(
                instance,
                "fiscal_year",
                None,
            ),
        )

        amount = attrs.get(
            "amount",
            getattr(
                instance,
                "amount",
                None,
            ),
        )

        # --------------------------------------------------------------
        # ACTIVITE OBLIGATOIRE
        # --------------------------------------------------------------

        if not activity:
            raise serializers.ValidationError({
                "activity":
                    "Veuillez sélectionner une activité."
            })

        # --------------------------------------------------------------
        # ACTIVITE / PROJET
        # --------------------------------------------------------------

        if activity and project:
            if activity.project_id != project.id:
                raise serializers.ValidationError({
                    "activity":
                        "L'activité doit appartenir au projet courant."
                })

        # --------------------------------------------------------------
        # SOUS-COMPOSANTE / PROJET
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
        # SOURCE DE FINANCEMENT
        # --------------------------------------------------------------

        if funding_source and project:
            if funding_source.project_id != project.id:
                raise serializers.ValidationError({
                    "funding_source":
                        "La source de financement doit appartenir "
                        "au projet courant."
                })

        # --------------------------------------------------------------
        # EXERCICE
        # --------------------------------------------------------------

        if fiscal_year is None:
            raise serializers.ValidationError({
                "fiscal_year":
                    "L'exercice est obligatoire."
            })

        if (
            fiscal_year < 2010
            or
            fiscal_year > 2090
        ):
            raise serializers.ValidationError({
                "fiscal_year":
                    "L'exercice doit être compris entre 2010 et 2090."
            })

        # --------------------------------------------------------------
        # MONTANT
        # --------------------------------------------------------------

        if amount is not None and amount < 0:
            raise serializers.ValidationError({
                "amount":
                    "Le montant programmé ne peut pas être négatif."
            })

        return attrs

    # ==================================================================
    # CREATION
    # ==================================================================

    def create(self, validated_data):

        activity = validated_data.get(
            "activity"
        )

        # La sous-composante est automatiquement celle de l'activité.
        if activity and activity.program_node_id:
            validated_data["program_node"] = activity.program_node

        return super().create(
            validated_data
        )

    # ==================================================================
    # MODIFICATION
    # ==================================================================

    def update(self, instance, validated_data):

        activity = validated_data.get(
            "activity",
            instance.activity,
        )

        if activity and activity.program_node_id:
            validated_data["program_node"] = activity.program_node

        return super().update(
            instance,
            validated_data,
        )


# ======================================================================
# EXECUTION FINANCIERE / TRANSACTIONS
# ======================================================================

class FinancialTransactionSerializer(serializers.ModelSerializer):

    # ------------------------------------------------------------------
    # LIGNE BUDGETAIRE
    # ------------------------------------------------------------------

    budget_line = serializers.PrimaryKeyRelatedField(
        queryset=BudgetLine.objects.all(),
        required=True,
        allow_null=False,
    )

    # ------------------------------------------------------------------
    # ACTIVITE
    # ------------------------------------------------------------------

    activity_id = serializers.IntegerField(
        source="budget_line.activity_id",
        read_only=True,
        allow_null=True,
    )

    activity_code = serializers.CharField(
        source="budget_line.activity.code",
        read_only=True,
        allow_null=True,
    )

    activity_title = serializers.CharField(
        source="budget_line.activity.title",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # COMPOSANTE
    # ------------------------------------------------------------------

    component_id = serializers.IntegerField(
        source="budget_line.program_node.parent_id",
        read_only=True,
        allow_null=True,
    )

    component_name = serializers.CharField(
        source="budget_line.program_node.parent.name",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # SOUS-COMPOSANTE
    # ------------------------------------------------------------------

    program_node_name = serializers.CharField(
        source="program_node.name",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # CATEGORIE DE DEPENSE
    # ------------------------------------------------------------------

    expense_category_name = serializers.CharField(
        source="expense_category.name",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # SOURCE DE FINANCEMENT
    # ------------------------------------------------------------------

    funding_source_name = serializers.CharField(
        source="funding_source.name",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # PROGRAMMATION
    # ------------------------------------------------------------------

    budget_amount = serializers.DecimalField(
        source="budget_line.amount",
        max_digits=18,
        decimal_places=2,
        read_only=True,
    )

    budget_note = serializers.CharField(
        source="budget_line.note",
        read_only=True,
        allow_null=True,
    )

    # ------------------------------------------------------------------
    # TYPE DE TRANSACTION
    # ------------------------------------------------------------------

    kind_label = serializers.CharField(
        source="get_kind_display",
        read_only=True,
    )

    class Meta:
        model = FinancialTransaction

        fields = [
            "id",
            "project",

            # Programmation financière
            "budget_line",
            "budget_amount",
            "budget_note",

            # Activité
            "activity_id",
            "activity_code",
            "activity_title",

            # Composante
            "component_id",
            "component_name",

            # Sous-composante
            "program_node",
            "program_node_name",

            # Catégorie
            "expense_category",
            "expense_category_name",

            # Source
            "funding_source",
            "funding_source_name",

            # Zone conservée dans la structure existante
            "geo_unit",

            # Transaction
            "kind",
            "kind_label",
            "date",
            "fiscal_year",
            "amount",
            "reference",
            "narrative",
            "supporting_doc",

            # Workflow / audit
            "status",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "project",

            "budget_amount",
            "budget_note",

            "activity_id",
            "activity_code",
            "activity_title",

            "component_id",
            "component_name",

            "program_node_name",
            "expense_category_name",
            "funding_source_name",

            "kind_label",

            "status",
            "created_at",
            "updated_at",
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

        budget_line = attrs.get(
            "budget_line",
            getattr(
                instance,
                "budget_line",
                None,
            ),
        )

        kind = attrs.get(
            "kind",
            getattr(
                instance,
                "kind",
                None,
            ),
        )

        date = attrs.get(
            "date",
            getattr(
                instance,
                "date",
                None,
            ),
        )

        fiscal_year = attrs.get(
            "fiscal_year",
            getattr(
                instance,
                "fiscal_year",
                None,
            ),
        )

        amount = attrs.get(
            "amount",
            getattr(
                instance,
                "amount",
                None,
            ),
        )

        # --------------------------------------------------------------
        # LIGNE BUDGETAIRE OBLIGATOIRE
        # --------------------------------------------------------------

        if not budget_line:
            raise serializers.ValidationError({
                "budget_line":
                    "Veuillez sélectionner une ligne budgétaire."
            })

        # --------------------------------------------------------------
        # LIGNE BUDGETAIRE / PROJET
        # --------------------------------------------------------------

        if budget_line and project:
            if budget_line.project_id != project.id:
                raise serializers.ValidationError({
                    "budget_line":
                        "La ligne budgétaire doit appartenir "
                        "au projet courant."
                })

        # --------------------------------------------------------------
        # EXERCICE
        # --------------------------------------------------------------

        if fiscal_year is None:
            raise serializers.ValidationError({
                "fiscal_year":
                    "L'exercice est obligatoire."
            })

        if fiscal_year < 2010 or fiscal_year > 2090:
            raise serializers.ValidationError({
                "fiscal_year":
                    "L'exercice doit être compris entre 2010 et 2090."
            })

        if (
            budget_line
            and budget_line.fiscal_year is not None
            and fiscal_year != budget_line.fiscal_year
        ):
            raise serializers.ValidationError({
                "fiscal_year":
                    "L'exercice doit correspondre à celui "
                    "de la programmation financière."
            })

        # --------------------------------------------------------------
        # DATE / EXERCICE
        # --------------------------------------------------------------

        if date and fiscal_year:
            if date.year != fiscal_year:
                raise serializers.ValidationError({
                    "date":
                        "L'année de la date doit correspondre "
                        "à l'exercice sélectionné."
                })

        # --------------------------------------------------------------
        # MONTANT
        # --------------------------------------------------------------

        if amount is None:
            raise serializers.ValidationError({
                "amount":
                    "Le montant est obligatoire."
            })

        if amount < 0:
            raise serializers.ValidationError({
                "amount":
                    "Le montant ne peut pas être négatif."
            })

        # --------------------------------------------------------------
        # TYPE
        # --------------------------------------------------------------

        valid_kinds = [
            FinancialTransaction.Kind.ENGAGEMENT,
            FinancialTransaction.Kind.DISBURSEMENT,
            FinancialTransaction.Kind.REALIZATION,
        ]

        if kind not in valid_kinds:
            raise serializers.ValidationError({
                "kind":
                    "Le type de transaction financière est invalide."
            })

        return attrs

    # ==================================================================
    # PREPARATION DES DONNEES
    #
    # Les informations structurelles sont récupérées depuis la
    # programmation financière afin d'éviter les incohérences.
    # ==================================================================

    def _prepare_from_budget_line(
        self,
        validated_data,
        budget_line,
    ):

        if not budget_line:
            return validated_data

        validated_data["program_node"] = (
            budget_line.program_node
        )

        validated_data["expense_category"] = (
            budget_line.expense_category
        )

        validated_data["funding_source"] = (
            budget_line.funding_source
        )

        validated_data["geo_unit"] = (
            budget_line.geo_unit
        )

        if budget_line.fiscal_year is not None:
            validated_data["fiscal_year"] = (
                budget_line.fiscal_year
            )

        return validated_data

    # ==================================================================
    # CREATION
    # ==================================================================

    def create(self, validated_data):

        budget_line = validated_data.get(
            "budget_line"
        )

        validated_data = self._prepare_from_budget_line(
            validated_data,
            budget_line,
        )

        return super().create(
            validated_data
        )

    # ==================================================================
    # MODIFICATION
    # ==================================================================

    def update(self, instance, validated_data):

        budget_line = validated_data.get(
            "budget_line",
            instance.budget_line,
        )

        validated_data = self._prepare_from_budget_line(
            validated_data,
            budget_line,
        )

        return super().update(
            instance,
            validated_data,
        )