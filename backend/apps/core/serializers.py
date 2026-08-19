from rest_framework import serializers

from .models import (
    Actor,
    Attachment,
    AuditLog,
    Milestone,
    Partner,
    Project,
    StateEvent,
    UnitOfMeasure,
)


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id",
            "code",
            "name",
            "full_name",
            "description",
            "currency_code",
            "currency_symbol",
            "start_date",
            "closing_date",
            "fiscal_year_start_month",
            "country",
            "funder",
            "logo",
            "default_locale",
            "grievance_sla_days",
            "public_dashboards_enabled",
            "is_active",
        ]


class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = [
            "id",
            "project",
            "code",
            "name",
            "target_date",
            "order",
        ]
        read_only_fields = ["project"]


class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = [
            "id",
            "project",
            "code",
            "name",
            "symbol",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "project",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = [
            "id",
            "project",
            "code",
            "name",
            "level",
            "phone",
            "email",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "project",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = [
            "id",
            "project",
            "code",
            "name",
            "phone",
            "email",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "project",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = [
            "id",
            "project",
            "content_type",
            "object_id",
            "file",
            "label",
            "uploaded_at",
        ]
        read_only_fields = [
            "project",
            "uploaded_at",
        ]


class StateEventSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(
        source="actor.username",
        read_only=True,
    )

    class Meta:
        model = StateEvent
        fields = [
            "id",
            "from_state",
            "to_state",
            "action",
            "actor_username",
            "at",
            "comment",
        ]


class AuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(
        source="actor.username",
        read_only=True,
    )

    model_name = serializers.CharField(
        source="content_type.model",
        read_only=True,
    )

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "project",
            "model_name",
            "object_id",
            "object_repr",
            "action",
            "actor",
            "actor_username",
            "at",
            "changes",
        ]

        read_only_fields = [
            "id",
            "project",
            "model_name",
            "object_id",
            "object_repr",
            "action",
            "actor",
            "actor_username",
            "at",
            "changes",
        ]