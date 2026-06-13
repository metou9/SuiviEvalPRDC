from decimal import Decimal

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import (
    Dimension,
    DimensionCategory,
    Indicator,
    IndicatorDimension,
    IndicatorResponsibility,
    IndicatorTarget,
    IndicatorType,
    Measurement,
    MeasurementValue,
)


class IndicatorTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndicatorType
        fields = ["id", "project", "code", "name", "order"]
        read_only_fields = ["project"]


class DimensionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DimensionCategory
        fields = ["id", "dimension", "code", "name", "order"]


class DimensionSerializer(serializers.ModelSerializer):
    categories = DimensionCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Dimension
        fields = ["id", "project", "code", "name", "order", "is_active", "categories"]
        read_only_fields = ["project"]


class IndicatorResponsibilitySerializer(serializers.ModelSerializer):
    role_code = serializers.CharField(source="role.code", read_only=True)

    class Meta:
        model = IndicatorResponsibility
        fields = ["id", "indicator", "responsibility", "role", "role_code", "user", "note"]


class IndicatorTargetSerializer(serializers.ModelSerializer):
    milestone_code = serializers.CharField(source="milestone.code", read_only=True)

    class Meta:
        model = IndicatorTarget
        fields = ["id", "indicator", "milestone", "milestone_code", "geo_unit", "value", "note"]


class IndicatorSerializer(serializers.ModelSerializer):
    indicator_type_code = serializers.CharField(source="indicator_type.code", read_only=True)
    dimension_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Dimension.objects.all(), write_only=True, required=False
    )
    responsibilities = IndicatorResponsibilitySerializer(many=True, read_only=True)
    targets = IndicatorTargetSerializer(many=True, read_only=True)

    class Meta:
        model = Indicator
        fields = [
            "id", "project", "code", "name", "definition", "indicator_type",
            "indicator_type_code", "program_node", "unit", "direction",
            "aggregation_method", "is_cri", "reporting_frequency", "data_source",
            "collection_tool", "is_active", "order", "dimensions", "dimension_ids",
            "responsibilities", "targets",
        ]
        read_only_fields = ["project", "dimensions"]

    def _sync_dimensions(self, indicator, dimension_ids):
        IndicatorDimension.objects.filter(indicator=indicator).delete()
        for dim in dimension_ids:
            IndicatorDimension.objects.create(indicator=indicator, dimension=dim)

    def create(self, validated_data):
        dimension_ids = validated_data.pop("dimension_ids", None)
        indicator = super().create(validated_data)
        if dimension_ids is not None:
            self._sync_dimensions(indicator, dimension_ids)
        return indicator

    def update(self, instance, validated_data):
        dimension_ids = validated_data.pop("dimension_ids", None)
        indicator = super().update(instance, validated_data)
        if dimension_ids is not None:
            self._sync_dimensions(indicator, dimension_ids)
        return indicator


class MeasurementValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementValue
        fields = ["id", "dimension_category", "value"]


class MeasurementSerializer(serializers.ModelSerializer):
    measurement_values = MeasurementValueSerializer(many=True, required=False)
    indicator_code = serializers.CharField(source="indicator.code", read_only=True)
    disaggregation_warning = serializers.SerializerMethodField()

    class Meta:
        model = Measurement
        fields = [
            "id", "project", "indicator", "indicator_code", "geo_unit", "program_node",
            "period_year", "period_quarter", "period_month", "period_date",
            "value", "source", "narrative", "status", "measurement_values",
            "disaggregation_warning", "created_at", "updated_at",
        ]
        read_only_fields = ["project", "status", "created_at", "updated_at"]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_disaggregation_warning(self, obj):
        values = list(obj.measurement_values.all())
        if not values:
            return None
        # Group by dimension; warn if any dimension's sum != measurement value.
        by_dim = {}
        for mv in values:
            dim_id = mv.dimension_category.dimension_id
            by_dim.setdefault(dim_id, Decimal("0"))
            by_dim[dim_id] += mv.value
        for total in by_dim.values():
            if total != obj.value:
                return "La somme des valeurs désagrégées ne correspond pas au total."
        return None

    def validate(self, attrs):
        # Disaggregation categories must belong to dimensions linked to the indicator.
        indicator = attrs.get("indicator") or getattr(self.instance, "indicator", None)
        values = attrs.get("measurement_values")
        if indicator and values:
            allowed = set(
                IndicatorDimension.objects.filter(indicator=indicator).values_list(
                    "dimension_id", flat=True
                )
            )
            for item in values:
                cat = item["dimension_category"]
                if allowed and cat.dimension_id not in allowed:
                    raise serializers.ValidationError(
                        {"measurement_values": f"'{cat}' is not a dimension of this indicator."}
                    )
        return attrs

    def _save_values(self, measurement, values):
        measurement.measurement_values.all().delete()
        for item in values:
            MeasurementValue.objects.create(measurement=measurement, **item)

    def create(self, validated_data):
        values = validated_data.pop("measurement_values", [])
        measurement = super().create(validated_data)
        self._save_values(measurement, values)
        return measurement

    def update(self, instance, validated_data):
        values = validated_data.pop("measurement_values", None)
        measurement = super().update(instance, validated_data)
        if values is not None:
            self._save_values(measurement, values)
        return measurement
