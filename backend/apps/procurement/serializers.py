from rest_framework import serializers

from .models import (
    PPMItem,
    ProcurementMethod,
    ProcurementProcess,
    ProcurementStage,
    StageEvent,
)


class ProcurementMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcurementMethod
        fields = ["id", "project", "parent", "code", "name", "order", "is_active"]
        read_only_fields = ["project"]


class ProcurementStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcurementStage
        fields = ["id", "project", "code", "name", "order"]
        read_only_fields = ["project"]


class PPMItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PPMItem
        fields = [
            "id", "project", "ppm_ref", "designation", "program_node",
            "expense_category", "procurement_method", "planned_amount",
            "planned_year", "is_active",
        ]
        read_only_fields = ["project"]


class StageEventSerializer(serializers.ModelSerializer):
    duration_days = serializers.IntegerField(read_only=True)
    stage_name = serializers.CharField(source="procurement_stage.name", read_only=True)
    stage_order = serializers.IntegerField(source="procurement_stage.order", read_only=True)

    class Meta:
        model = StageEvent
        fields = [
            "id", "procurement_process", "procurement_stage", "stage_name", "stage_order",
            "start_date", "end_date", "decision", "deadline", "duration_days",
        ]


class ProcurementProcessSerializer(serializers.ModelSerializer):
    stage_events = StageEventSerializer(many=True, read_only=True)
    current_stage_name = serializers.CharField(source="current_stage.name", read_only=True)

    class Meta:
        model = ProcurementProcess
        fields = [
            "id", "project", "ppm_item", "designation", "procurement_method",
            "expense_category", "program_node", "geo_unit", "estimated_amount",
            "awarded_amount", "supplier", "current_stage", "current_stage_name",
            "is_completed", "status", "stage_events", "created_at", "updated_at",
        ]
        read_only_fields = ["project", "status", "created_at", "updated_at"]
