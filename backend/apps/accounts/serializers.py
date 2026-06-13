from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ProjectMembership, Role, RoleAssignment

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "code", "name", "description", "is_system"]


class RoleAssignmentSerializer(serializers.ModelSerializer):
    role_code = serializers.CharField(source="role.code", read_only=True)

    class Meta:
        model = RoleAssignment
        fields = [
            "id", "user", "role", "role_code", "project",
            "scope_geo", "scope_program", "is_active",
        ]
        read_only_fields = ["project"]


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "display_name", "phone", "default_locale", "is_active", "password",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class MembershipSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="project.code", read_only=True)
    name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = ProjectMembership
        fields = ["project", "code", "name", "is_default"]
