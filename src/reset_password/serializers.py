from rest_framework import serializers


# =========================
# REQUEST RESET
# =========================
class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer pour demander un code de réinitialisation.
    """

    email = serializers.EmailField()


# =========================
# VERIFY CODE
# =========================
class PasswordResetVerifySerializer(serializers.Serializer):
    """
    Serializer pour vérifier le code OTP.
    """

    email = serializers.EmailField()
    code = serializers.CharField(
        max_length=6,
        min_length=6,
    )


# =========================
# CONFIRM RESET PASSWORD
# =========================
class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer pour confirmer la réinitialisation du mot de passe.
    """

    email = serializers.EmailField()
    code = serializers.CharField(
        max_length=6,
        min_length=6,
    )
    new_password = serializers.CharField(
        min_length=8,
        write_only=True,
    )

    def validate_new_password(self, value):
        """
        Optionnel : règles de sécurité mot de passe
        """
        if value.isdigit():
            raise serializers.ValidationError(
                "Le mot de passe ne peut pas être uniquement numérique."
            )
        return value
