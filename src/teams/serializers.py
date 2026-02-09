from rest_framework import serializers

from .models import Teams


class TeamsSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)

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

    def get_full_name(self, obj):
        """Méthode helper si owner.get_full_name() n'existe pas"""
        if obj.owner:
            return f"{obj.owner.first_name} {obj.owner.last_name}"
        return None
