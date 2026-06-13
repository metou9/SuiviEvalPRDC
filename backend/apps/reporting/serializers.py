from rest_framework import serializers

from .models import Report, ReportTemplate


class ReportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = ["id", "project", "code", "name", "structure"]
        read_only_fields = ["project"]


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            "id", "project", "template", "title", "period_year", "period_quarter",
            "generated_at", "generated_by", "status", "file",
        ]
        read_only_fields = ["project", "generated_at", "generated_by", "file", "status"]
