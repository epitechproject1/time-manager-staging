from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Department

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email"]


class DepartmentLiteSerializer(serializers.ModelSerializer):
    director = UserMiniSerializer(read_only=True)
    teams_count = serializers.IntegerField(read_only=True)
    is_pinned = serializers.IntegerField(read_only=True)

    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "description",
            "director",
            "is_active",
            "is_pinned",
            "teams_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DepartmentSerializer(serializers.ModelSerializer):
    director = UserMiniSerializer(read_only=True)
    director_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="director",
        write_only=True,
        required=False,
        allow_null=True,
    )

    teams_count = serializers.IntegerField(read_only=True)
    employees_count = serializers.IntegerField(read_only=True)
    is_pinned = serializers.IntegerField(read_only=True)

    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "description",
            "director",
            "director_id",
            "is_active",
            "is_pinned",
            "teams_count",
            "employees_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value):
        value = (value or "").strip()
        if not value:
            raise ValidationError("Le nom du département est obligatoire.")

        instance = getattr(self, "instance", None)
        qs = Department.objects.filter(name__iexact=value)
        if instance:
            qs = qs.exclude(pk=instance.pk)

        if qs.exists():
            raise ValidationError(
                f"Un département portant le nom « {value} » existe déjà."
            )

        return value
