from datetime import date

from django.utils import timezone
from rest_framework import serializers

from .constants import PermissionType
from .models import Permission


class PermissionSerializer(serializers.ModelSerializer):
    """
    Serializer de lecture (list / retrieve).
    """

    permission_type = serializers.ChoiceField(
        choices=PermissionType.choices,
        read_only=True,
    )

    granted_by_user = serializers.StringRelatedField(read_only=True)
    granted_to_user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Permission
        fields = [
            "id",
            "permission_type",
            "start_date",
            "end_date",
            "granted_by_user",
            "granted_to_user",
            "created_at",
            "updated_at",
        ]


class PermissionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer de création d'une permission.
    """

    class Meta:
        model = Permission
        fields = [
            "permission_type",
            "start_date",
            "end_date",
            "granted_to_user",
        ]

    def validate(self, attrs):
        start_date = attrs["start_date"]
        end_date = attrs.get("end_date")
        today = timezone.now().date()

        if start_date < today:
            raise serializers.ValidationError(
                "La date de début ne peut pas être dans le passé."
            )

        if end_date and end_date < start_date:
            raise serializers.ValidationError(
                "La date de fin ne peut pas être antérieure à la date de début."
            )

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")

        if request is None or request.user.is_anonymous:
            raise serializers.ValidationError("Utilisateur non authentifié.")

        validated_data["granted_by_user"] = request.user
        return super().create(validated_data)


class PermissionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer de mise à jour (PATCH / PUT) d'une permission.
    """

    class Meta:
        model = Permission
        fields = [
            "permission_type",
            "start_date",
            "end_date",
        ]

    def validate(self, attrs):
        instance = self.instance
        today = timezone.now().date()

        # 🔒 Reconstruction de l'état final (OBLIGATOIRE en PATCH)
        start_date = attrs.get("start_date", instance.start_date)
        end_date = attrs.get("end_date", instance.end_date)

        # 🔒 Sécurisation ultime des types
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)

        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)

        if start_date < today:
            raise serializers.ValidationError(
                "La date de début ne peut pas être dans le passé."
            )

        if end_date and end_date < start_date:
            raise serializers.ValidationError(
                "La date de fin ne peut pas être antérieure à la date de début."
            )

        return attrs
