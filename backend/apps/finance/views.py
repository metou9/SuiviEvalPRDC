from rest_framework import status
from rest_framework.response import Response

from apps.accounts.permissions import ReadOrCapability, WorkflowObjectPermission
from apps.core.api import AuthoredModelViewSet, ExportMixin, WorkflowActionsMixin

from .models import BudgetLine, ExpenseCategory, FinancialTransaction, FundingSource
from .serializers import (
    BudgetLineSerializer,
    ExpenseCategorySerializer,
    FinancialTransactionSerializer,
    FundingSourceSerializer,
)


class ExpenseCategoryViewSet(AuthoredModelViewSet):
    serializer_class = ExpenseCategorySerializer
    queryset = ExpenseCategory.objects.all()
    permission_classes = [ReadOrCapability]
    write_capability = "config.manage"
    filterset_fields = ["code", "is_active"]
    search_fields = ["code", "name"]


class FundingSourceViewSet(AuthoredModelViewSet):
    serializer_class = FundingSourceSerializer
    queryset = FundingSource.objects.all()
    permission_classes = [ReadOrCapability]
    write_capability = "config.manage"
    filterset_fields = ["code", "is_active"]
    search_fields = ["code", "name"]


class BudgetLineViewSet(ExportMixin, AuthoredModelViewSet):
    serializer_class = BudgetLineSerializer
    queryset = BudgetLine.objects.select_related(
        "program_node", "expense_category", "geo_unit", "funding_source"
    ).all()
    permission_classes = [ReadOrCapability]
    write_capability = "financialtransaction.create"
    geo_scope_field = "geo_unit"
    filterset_fields = ["program_node", "expense_category", "geo_unit", "funding_source", "fiscal_year"]
    ordering_fields = ["fiscal_year", "amount"]


class FinancialTransactionViewSet(ExportMixin, WorkflowActionsMixin, AuthoredModelViewSet):
    serializer_class = FinancialTransactionSerializer
    queryset = FinancialTransaction.objects.select_related(
        "program_node", "expense_category", "geo_unit", "funding_source"
    ).all()
    permission_classes = [WorkflowObjectPermission]
    workflow_area = "financialtransaction"
    geo_scope_field = "geo_unit"
    filterset_fields = {
        "kind": ["exact"],
        "program_node": ["exact"],
        "expense_category": ["exact"],
        "geo_unit": ["exact"],
        "funding_source": ["exact"],
        "fiscal_year": ["exact"],
        "status": ["exact"],
    }
    search_fields = ["reference", "narrative"]
    ordering_fields = ["date", "amount", "fiscal_year"]
    ordering = ["-date"]

    def consolidate(self, request, pk=None):
        obj = self.get_object()
        if obj.kind == FinancialTransaction.Kind.REALIZATION and not obj.supporting_doc:
            return Response(
                {"detail": "Un justificatif est requis pour consolider une réalisation."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self._do_transition(request, "consolidate")
