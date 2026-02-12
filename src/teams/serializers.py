from django.contrib.auth import get_user_model
from rest_framework import serializers

from departments.models import Department

from .models import Teams

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email"]


class DepartmentMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name"]


class TeamsSerializer(serializers.ModelSerializer):
    owner = UserMiniSerializer(read_only=True)
    department = DepartmentMiniSerializer(read_only=True)

    owner_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )
    department_id = serializers.IntegerField(write_only=True, required=True)

    members = UserMiniSerializer(many=True, read_only=True)
    members_count = serializers.SerializerMethodField()

    members_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = Teams
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "owner_id",
            "department",
            "department_id",
            "members",
            "members_ids",
            "members_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "members_count"]

    def get_members_count(self, obj):
        return obj.members.count()

    def create(self, validated_data):
        owner_id = validated_data.pop("owner_id", None)
        department_id = validated_data.pop("department_id")
        members_ids = validated_data.pop("members_ids", [])

        request = self.context.get("request")
        if owner_id is None and request and request.user.is_authenticated:
            owner_id = request.user.id

        team = Teams.objects.create(
            owner_id=owner_id, department_id=department_id, **validated_data
        )

        if members_ids:
            team.members.set(User.objects.filter(id__in=members_ids))

        if team.owner_id:
            team.members.add(team.owner_id)

        return team

    def update(self, instance, validated_data):
        owner_id = validated_data.pop("owner_id", None)
        department_id = validated_data.pop("department_id", None)
        members_ids = validated_data.pop("members_ids", None)

        if owner_id is not None:
            instance.owner_id = owner_id
        if department_id is not None:
            instance.department_id = department_id

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if members_ids is not None:
            instance.members.set(User.objects.filter(id__in=members_ids))

        return instance
