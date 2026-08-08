from rest_framework import serializers

from .models import Activity, ActivityParticipant


class ActivityParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityParticipant
        fields = ["id", "full_name", "origin", "organization", "function", "sex"]


class ActivitySerializer(serializers.ModelSerializer):
    participants = ActivityParticipantSerializer(many=True, required=False)
    program_node_code = serializers.CharField(source="program_node.code", read_only=True)
    program_node_name = serializers.CharField(source="program_node.name", read_only=True)
    indicator_code = serializers.CharField(source="indicator.code", read_only=True)
    indicator_name = serializers.CharField(source="indicator.name", read_only=True)
    geo_unit_name = serializers.CharField(source="geo_unit.name", read_only=True)

    class Meta:
        model = Activity
        fields = [
            "id", "project", "kind", "geo_unit", "geo_unit_name",
            "program_node", "program_node_code", "program_node_name",
            "indicator", "indicator_code", "indicator_name", "title", "date", "location", "organizer", "duration_hours", "objective",
            "description", "total_participants", "women_count", "youth_count",
            "submission_date", "funding_requested", "funding_obtained", "funding_date",
            "management_committee", "beneficiary_org", "actor_name", "implantation_date",
            "main_actions", "status", "participants", "created_at", "updated_at",
        ]
        read_only_fields = ["project", "status", "created_at", "updated_at"]


    def validate(self, attrs):
        program_node = attrs.get("program_node") or getattr(self.instance, "program_node", None)
        indicator = attrs.get("indicator") or getattr(self.instance, "indicator", None)

        if indicator and program_node and indicator.program_node_id:
            # An indicator linked to a program node must belong to the selected node
            # or to one of its descendants. This prevents cross-component reporting.
            allowed_ids = {program_node.id}
            frontier = [program_node.id]
            from apps.program.models import ProgramNode
            while frontier:
                children = list(
                    ProgramNode.objects.filter(parent_id__in=frontier).values_list("id", flat=True)
                )
                allowed_ids.update(children)
                frontier = children
            if indicator.program_node_id not in allowed_ids:
                raise serializers.ValidationError({
                    "indicator": "Cet indicateur n'appartient pas à la composante/sous-composante sélectionnée."
                })
        return attrs

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
