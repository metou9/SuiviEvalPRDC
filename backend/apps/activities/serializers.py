from rest_framework import serializers

from .models import Activity, ActivityParticipant


class ActivityParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityParticipant
        fields = ["id", "full_name", "origin", "organization", "function", "sex"]


class ActivitySerializer(serializers.ModelSerializer):
    participants = ActivityParticipantSerializer(many=True, required=False)

    class Meta:
        model = Activity
        fields = [
            "id", "project", "kind", "geo_unit", "program_node", "indicator",
            "title", "date", "location", "organizer", "duration_hours", "objective",
            "description", "total_participants", "women_count", "youth_count",
            "submission_date", "funding_requested", "funding_obtained", "funding_date",
            "management_committee", "beneficiary_org", "actor_name", "implantation_date",
            "main_actions", "status", "participants", "created_at", "updated_at",
        ]
        read_only_fields = ["project", "status", "created_at", "updated_at"]

    def _save_participants(self, activity, participants):
        activity.participants.all().delete()
        for item in participants:
            ActivityParticipant.objects.create(activity=activity, **item)

    def create(self, validated_data):
        participants = validated_data.pop("participants", [])
        activity = super().create(validated_data)
        self._save_participants(activity, participants)
        return activity

    def update(self, instance, validated_data):
        participants = validated_data.pop("participants", None)
        activity = super().update(instance, validated_data)
        if participants is not None:
            self._save_participants(activity, participants)
        return activity
