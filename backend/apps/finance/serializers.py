from rest_framework import serializers

from .models import BudgetLine, ExpenseCategory, FinancialTransaction, FundingSource


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ["id", "project", "code", "name", "order", "is_active"]
        read_only_fields = ["project"]


class FundingSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundingSource
        fields = ["id", "project", "code", "name", "is_active"]
        read_only_fields = ["project"]


class BudgetLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetLine
        fields = [
            "id", "project", "program_node", "expense_category", "geo_unit",
            "funding_source", "fiscal_year", "amount", "note",
        ]
        read_only_fields = ["project"]


class FinancialTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialTransaction
        fields = [
            "id", "project", "program_node", "expense_category", "geo_unit",
            "funding_source", "kind", "date", "fiscal_year", "amount", "reference",
            "narrative", "supporting_doc", "status", "created_at", "updated_at",
        ]
        read_only_fields = ["project", "status", "created_at", "updated_at"]
