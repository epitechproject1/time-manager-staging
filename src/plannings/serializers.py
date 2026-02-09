from rest_framework import serializers

from users.constants import UserRole

from .models import Planning


class PlanningSerializer(serializers.ModelSerializer):
    class Meta:
        model = Planning
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        start_dt = attrs.get("start_datetime") or getattr(
            self.instance,
            "start_datetime",
            None,
        )
        end_dt = attrs.get("end_datetime") or getattr(
            self.instance,
            "end_datetime",
            None,
        )

        if start_dt and end_dt and end_dt <= start_dt:
            raise serializers.ValidationError(
                {
                    "end_datetime": (
                        "end_datetime doit être strictement après start_datetime."
                    ),
                }
            )

        return attrs

    def validate_user(self, value):
        """
        Empêche un USER de créer/modifier un planning pour quelqu’un d’autre.
        Admin peut choisir user librement.
        """
        request = self.context.get("request")

        if not request or not request.user or not request.user.is_authenticated:
            return value

        if request.user.role == UserRole.ADMIN:
            return value

        if value.id != request.user.id:
            raise serializers.ValidationError(
                "Vous ne pouvez créer/modifier que vos propres plannings."
            )

        return value
