from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Department

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email"]


class DepartmentSerializer(serializers.ModelSerializer):
    director = UserMiniSerializer(read_only=True)
    director_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "description",
            "director",
            "director_id",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        director_id = validated_data.pop("director_id", None)
        return Department.objects.create(director_id=director_id, **validated_data)

    def update(self, instance, validated_data):
        director_id = validated_data.pop("director_id", None)

        if director_id is not None:
            instance.director_id = director_id

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
