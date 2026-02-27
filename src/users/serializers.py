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
            "is_active",
            "last_login",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "role",
            "is_active",
            "last_login",
            "created_at",
            "updated_at",
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer de création utilisateur.
    """

    password = serializers.CharField(write_only=True)

    role = serializers.ChoiceField(choices=UserRole.choices)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "role",
            "password",
        ]

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Un utilisateur avec cet email existe déjà."
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer de mise à jour utilisateur.
    """

    role = serializers.ChoiceField(
        choices=UserRole.choices,
        required=False,
    )

    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "is_active",
        ]

    def validate_role(self, value):
        """
        Empêche un utilisateur non-admin de modifier son rôle.
        """
        request = self.context.get("request")

        if request and request.user.role != UserRole.ADMIN:
            raise serializers.ValidationError(
                "Vous n'êtes pas autorisé à modifier le rôle."
            )

        return value

    def validate_is_active(self, value):
        """
        Empêche un utilisateur non-admin de modifier l'état du compte.
        """
        request = self.context.get("request")

        if request and request.user.role != UserRole.ADMIN:
            raise serializers.ValidationError(
                "Seul un administrateur peut modifier l'état du compte."
            )

        return value
