from decimal import Decimal

from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import (
    ReadOrCapability,
    WorkflowObjectPermission,
)
from apps.core.api import (
    AuthoredModelViewSet,
    ExportMixin,
    WorkflowActionsMixin,
)

from .models import (
    BudgetLine,
    ExpenseCategory,
    FinancialTransaction,
    FundingSource,
)
from .serializers import (
    BudgetLineSerializer,
    ExpenseCategorySerializer,
    FinancialTransactionSerializer,
    FundingSourceSerializer,
)


# ======================================================================
# CATEGORIES DE DEPENSES
# ======================================================================

class ExpenseCategoryViewSet(AuthoredModelViewSet):
    serializer_class = ExpenseCategorySerializer
    queryset = ExpenseCategory.objects.all()
    permission_classes = [ReadOrCapability]
    write_capability = "reference.manage"

    filterset_fields = [
        "code",
        "is_active",
    ]

    search_fields = [
        "code",
        "name",
    ]


# ======================================================================
# SOURCES DE FINANCEMENT
# ======================================================================

class FundingSourceViewSet(AuthoredModelViewSet):
    serializer_class = FundingSourceSerializer
    queryset = FundingSource.objects.all()
    permission_classes = [ReadOrCapability]
    write_capability = "reference.manage"

    filterset_fields = [
        "code",
        "is_active",
    ]

    search_fields = [
        "code",
        "name",
    ]


# ======================================================================
# PROGRAMMATION FINANCIERE / LIGNES BUDGETAIRES
# ======================================================================

class BudgetLineViewSet(
    ExportMixin,
    AuthoredModelViewSet,
):
    serializer_class = BudgetLineSerializer

    queryset = BudgetLine.objects.select_related(
        "activity",
        "program_node",
        "program_node__parent",
        "expense_category",
        "geo_unit",
        "funding_source",
    ).all()

    permission_classes = [
        ReadOrCapability,
    ]

    write_capability = "financialtransaction.create"

    geo_scope_field = "geo_unit"

    filterset_fields = [
        "activity",
        "program_node",
        "expense_category",
        "geo_unit",
        "funding_source",
        "fiscal_year",
    ]

    search_fields = [
        "activity__code",
        "activity__title",
        "program_node__code",
        "program_node__name",
        "expense_category__code",
        "expense_category__name",
        "funding_source__code",
        "funding_source__name",
        "note",
    ]

    ordering_fields = [
        "fiscal_year",
        "amount",
        "activity__title",
    ]

    ordering = [
        "-fiscal_year",
        "activity__title",
    ]

    # ==================================================================
    # SUIVI FINANCIER
    #
    # Retourne le suivi financier par ligne budgétaire :
    #
    # - budget programmé
    # - engagements
    # - décaissements
    # - réalisations / dépenses justifiées
    # - solde
    # - taux d'engagement
    # - taux de décaissement
    # - taux de réalisation financière
    #
    # URL :
    # /api/v1/budget-lines/financial-monitoring/
    # ==================================================================

    @action(
        detail=False,
        methods=["get"],
        url_path="financial-monitoring",
    )
    def financial_monitoring(self, request):

        # --------------------------------------------------------------
        # BASE QUERYSET
        #
        # On passe par filter_queryset afin de conserver :
        # - le projet courant
        # - les permissions
        # - les filtres DRF
        # - le scope géographique
        # --------------------------------------------------------------

        queryset = self.filter_queryset(
            self.get_queryset()
        )

        # --------------------------------------------------------------
        # FILTRES COMPLEMENTAIRES
        # --------------------------------------------------------------

        activity = request.query_params.get(
            "activity"
        )

        component = request.query_params.get(
            "component"
        )

        program_node = request.query_params.get(
            "program_node"
        )

        expense_category = request.query_params.get(
            "expense_category"
        )

        funding_source = request.query_params.get(
            "funding_source"
        )

        fiscal_year = request.query_params.get(
            "fiscal_year"
        )

        # --------------------------------------------------------------
        # ACTIVITE
        # --------------------------------------------------------------

        if activity:
            queryset = queryset.filter(
                activity_id=activity
            )

        # --------------------------------------------------------------
        # COMPOSANTE
        #
        # BudgetLine.program_node = sous-composante
        # program_node.parent = composante
        # --------------------------------------------------------------

        if component:
            queryset = queryset.filter(
                program_node__parent_id=component
            )

        # --------------------------------------------------------------
        # SOUS-COMPOSANTE
        # --------------------------------------------------------------

        if program_node:
            queryset = queryset.filter(
                program_node_id=program_node
            )

        # --------------------------------------------------------------
        # CATEGORIE DE DEPENSE
        # --------------------------------------------------------------

        if expense_category:
            queryset = queryset.filter(
                expense_category_id=expense_category
            )

        # --------------------------------------------------------------
        # SOURCE DE FINANCEMENT
        # --------------------------------------------------------------

        if funding_source:
            queryset = queryset.filter(
                funding_source_id=funding_source
            )

        # --------------------------------------------------------------
        # EXERCICE
        # --------------------------------------------------------------

        if fiscal_year:
            queryset = queryset.filter(
                fiscal_year=fiscal_year
            )

        # --------------------------------------------------------------
        # AGREGATION DES TRANSACTIONS
        # --------------------------------------------------------------

        decimal_output = DecimalField(
            max_digits=18,
            decimal_places=2,
        )

        queryset = queryset.annotate(

            # ----------------------------------------------------------
            # ENGAGEMENTS CONSOLIDES
            # ----------------------------------------------------------

            total_engagements=Coalesce(
                Sum(
                    "transactions__amount",
                    filter=Q(
                        transactions__kind=(
                            FinancialTransaction.Kind.ENGAGEMENT
                        ),
                        transactions__status="CONSOLIDATED",
                    ),
                ),
                Value(
                    Decimal("0.00"),
                    output_field=decimal_output,
                ),
            ),

            # ----------------------------------------------------------
            # DECAISSEMENTS CONSOLIDES
            # ----------------------------------------------------------

            total_disbursements=Coalesce(
                Sum(
                    "transactions__amount",
                    filter=Q(
                        transactions__kind=(
                            FinancialTransaction.Kind.DISBURSEMENT
                        ),
                        transactions__status="CONSOLIDATED",
                    ),
                ),
                Value(
                    Decimal("0.00"),
                    output_field=decimal_output,
                ),
            ),

            # ----------------------------------------------------------
            # DEPENSES JUSTIFIEES CONSOLIDEES
            # ----------------------------------------------------------

            total_realizations=Coalesce(
                Sum(
                    "transactions__amount",
                    filter=Q(
                        transactions__kind=(
                            FinancialTransaction.Kind.REALIZATION
                        ),
                        transactions__status="CONSOLIDATED",
                    ),
                ),
                Value(
                    Decimal("0.00"),
                    output_field=decimal_output,
                ),
            ),
        )

        queryset = queryset.order_by(
            "-fiscal_year",
            "activity__title",
            "id",
        )

        # --------------------------------------------------------------
        # CONSTRUCTION DU RESULTAT
        # --------------------------------------------------------------

        results = []

        for budget_line in queryset:

            budget_amount = (
                budget_line.amount
                or Decimal("0.00")
            )

            engagements = (
                budget_line.total_engagements
                or Decimal("0.00")
            )

            disbursements = (
                budget_line.total_disbursements
                or Decimal("0.00")
            )

            realizations = (
                budget_line.total_realizations
                or Decimal("0.00")
            )

            # ----------------------------------------------------------
            # SOLDE
            #
            # Selon le suivi financier :
            # budget programmé - réalisations financières
            # ----------------------------------------------------------

            balance = (
                budget_amount
                - realizations
            )

            # ----------------------------------------------------------
            # TAUX
            # ----------------------------------------------------------

            if budget_amount > 0:

                commitment_rate = (
                    engagements
                    / budget_amount
                    * Decimal("100")
                )

                disbursement_rate = (
                    disbursements
                    / budget_amount
                    * Decimal("100")
                )

                financial_realization_rate = (
                    realizations
                    / budget_amount
                    * Decimal("100")
                )

            else:

                commitment_rate = Decimal("0.00")
                disbursement_rate = Decimal("0.00")
                financial_realization_rate = Decimal("0.00")

            # ----------------------------------------------------------
            # ACTIVITE
            # ----------------------------------------------------------

            activity_obj = budget_line.activity

            # ----------------------------------------------------------
            # SOUS-COMPOSANTE / COMPOSANTE
            # ----------------------------------------------------------

            program_node_obj = (
                budget_line.program_node
            )

            component_obj = (
                program_node_obj.parent
                if program_node_obj
                else None
            )

            # ----------------------------------------------------------
            # CATEGORIE
            # ----------------------------------------------------------

            expense_category_obj = (
                budget_line.expense_category
            )

            # ----------------------------------------------------------
            # SOURCE
            # ----------------------------------------------------------

            funding_source_obj = (
                budget_line.funding_source
            )

            # ----------------------------------------------------------
            # RESULTAT
            # ----------------------------------------------------------

            results.append({
                "budget_line": budget_line.id,

                # Activité
                "activity": (
                    activity_obj.id
                    if activity_obj
                    else None
                ),
                "activity_code": (
                    activity_obj.code
                    if activity_obj
                    else None
                ),
                "activity_title": (
                    activity_obj.title
                    if activity_obj
                    else None
                ),

                # Composante
                "component": (
                    component_obj.id
                    if component_obj
                    else None
                ),
                "component_name": (
                    component_obj.name
                    if component_obj
                    else None
                ),

                # Sous-composante
                "program_node": (
                    program_node_obj.id
                    if program_node_obj
                    else None
                ),
                "program_node_name": (
                    program_node_obj.name
                    if program_node_obj
                    else None
                ),

                # Catégorie
                "expense_category": (
                    expense_category_obj.id
                    if expense_category_obj
                    else None
                ),
                "expense_category_name": (
                    expense_category_obj.name
                    if expense_category_obj
                    else None
                ),

                # Source
                "funding_source": (
                    funding_source_obj.id
                    if funding_source_obj
                    else None
                ),
                "funding_source_name": (
                    funding_source_obj.name
                    if funding_source_obj
                    else None
                ),

                # Exercice
                "fiscal_year":
                    budget_line.fiscal_year,

                # Montants
                "budget_amount":
                    budget_amount,

                "engagements":
                    engagements,

                "disbursements":
                    disbursements,

                "realizations":
                    realizations,

                "balance":
                    balance,

                # Taux
                "commitment_rate":
                    round(
                        commitment_rate,
                        2,
                    ),

                "disbursement_rate":
                    round(
                        disbursement_rate,
                        2,
                    ),

                "financial_realization_rate":
                    round(
                        financial_realization_rate,
                        2,
                    ),

                # Observation programmation
                "note":
                    budget_line.note,
            })

        return Response(
            results,
            status=status.HTTP_200_OK,
        )


# ======================================================================
# EXECUTION FINANCIERE / TRANSACTIONS
# ======================================================================

class FinancialTransactionViewSet(
    ExportMixin,
    WorkflowActionsMixin,
    AuthoredModelViewSet,
):
    serializer_class = FinancialTransactionSerializer

    queryset = FinancialTransaction.objects.select_related(
        "budget_line",
        "budget_line__activity",
        "budget_line__program_node",
        "budget_line__program_node__parent",
        "program_node",
        "expense_category",
        "geo_unit",
        "funding_source",
    ).all()

    permission_classes = [
        WorkflowObjectPermission,
    ]

    workflow_area = "financialtransaction"

    geo_scope_field = "geo_unit"

    filterset_fields = {
        "budget_line": [
            "exact",
        ],
        "budget_line__activity": [
            "exact",
        ],
        "kind": [
            "exact",
        ],
        "program_node": [
            "exact",
        ],
        "expense_category": [
            "exact",
        ],
        "geo_unit": [
            "exact",
        ],
        "funding_source": [
            "exact",
        ],
        "fiscal_year": [
            "exact",
        ],
        "status": [
            "exact",
        ],
    }

    search_fields = [
        "reference",
        "narrative",
        "budget_line__activity__code",
        "budget_line__activity__title",
    ]

    ordering_fields = [
        "date",
        "amount",
        "fiscal_year",
    ]

    ordering = [
        "-date",
    ]

    # ==================================================================
    # CONSOLIDATION
    # ==================================================================

    def consolidate(
        self,
        request,
        pk=None,
    ):

        obj = self.get_object()

        # --------------------------------------------------------------
        # JUSTIFICATIF OBLIGATOIRE POUR UNE REALISATION
        # --------------------------------------------------------------

        if (
            obj.kind
            == FinancialTransaction.Kind.REALIZATION
            and
            not obj.supporting_doc
        ):
            return Response(
                {
                    "detail":
                        "Un justificatif est requis pour "
                        "consolider une réalisation."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self._do_transition(
            request,
            "consolidate",
        )