from rest_framework import serializers

from .constants import UserRole
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer de lecture (list / retrieve).
    """

    role = serializers.ChoiceField(
        choices=UserRole.choices,
        read_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "role",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "role",
            "created_at",
            "updated_at",
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer de création utilisateur.
    """

    role = serializers.ChoiceField(choices=UserRole.choices)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "role",
        ]

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Un utilisateur avec cet email existe déjà."
            )
        return value


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer de mise à jour utilisateur.
    """

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "role",
        ]