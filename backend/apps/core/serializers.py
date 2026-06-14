from rest_framework import serializers

from .models import Attachment, Milestone, Project, StateEvent


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id", "code", "name", "full_name", "description",
            "currency_code", "currency_symbol", "start_date", "closing_date",
            "fiscal_year_start_month", "country", "funder", "logo",
            "default_locale", "grievance_sla_days", "public_dashboards_enabled",
            "is_active",
        ]


class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = ["id", "project", "code", "name", "target_date", "order"]
        read_only_fields = ["project"]


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["id", "project", "content_type", "object_id", "file", "label", "uploaded_at"]
        read_only_fields = ["project", "uploaded_at"]


class StateEventSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = StateEvent
        fields = ["id", "from_state", "to_state", "action", "actor_username", "at", "comment"]
