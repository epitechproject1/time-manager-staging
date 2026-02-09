from rest_framework import serializers

from .models import Teams


class TeamsSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()
    owner_email = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()

    class Meta:
        model = Teams
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "owner_name",
            "owner_email",
            "department",
            "department_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_owner_name(self, obj):
        if obj.owner:
            return f"{obj.owner.first_name} {obj.owner.last_name}".strip()
        return None

    def get_owner_email(self, obj):
        return obj.owner.email if obj.owner else None

    def get_department_name(self, obj):
        return obj.department.name if obj.department else None
