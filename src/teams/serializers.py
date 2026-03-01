from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

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


class TeamsLiteSerializer(serializers.ModelSerializer):
    """
    Annuaire (visible par tous)
    """

    owner = UserMiniSerializer(read_only=True)
    department = DepartmentMiniSerializer(read_only=True)
    members_count = serializers.SerializerMethodField()
    is_pinned = serializers.IntegerField(read_only=True)

    class Meta:
        model = Teams
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "department",
            "members_count",
            "is_pinned",
        ]

    def get_members_count(self, obj):
        annotated = getattr(obj, "members_count", None)
        if annotated is not None:
            return annotated
        return obj.members.count()


class TeamsSerializer(serializers.ModelSerializer):

    owner = UserMiniSerializer(read_only=True)
    department = DepartmentMiniSerializer(read_only=True)

    owner_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )
    department_id = serializers.IntegerField(write_only=True, required=False)

    members = UserMiniSerializer(many=True, read_only=True)
    members_count = serializers.SerializerMethodField()

    members_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
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
        annotated = getattr(obj, "members_count", None)
        if annotated is not None:
            return annotated
        return obj.members.count()

    def create(self, validated_data):
        owner_id = validated_data.pop("owner_id", None)
        department_id = validated_data.pop("department_id", None)
        members_ids = validated_data.pop("members_ids", [])

        if department_id is None:
            raise ValidationError({"department_id": "department_id est obligatoire."})

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

    def validate_name(self, value):
        value = (value or "").strip()
        if not value:
            raise ValidationError("Le nom de l'équipe est obligatoire.")

        instance = getattr(self, "instance", None)
        qs = Teams.objects.filter(name__iexact=value)

        if instance:
            qs = qs.exclude(pk=instance.pk)

        if qs.exists():
            raise ValidationError(f"Une équipe portant le nom « {value} » existe déjà.")

        return value

    def update(self, instance, validated_data):
        owner_id = validated_data.pop("owner_id", None)
        department_id = validated_data.pop("department_id", None)
        members_ids = validated_data.pop("members_ids", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if owner_id is not None:
            instance.owner_id = owner_id

        if department_id is not None:
            instance.department_id = department_id

        instance.save()

        if members_ids is not None:
            instance.members.set(User.objects.filter(id__in=members_ids))
            if instance.owner_id:
                instance.members.add(instance.owner_id)

        return instance

    def validate(self, attrs):

        instance = getattr(self, "instance", None)

        current_owner_id = instance.owner_id if instance else None
        new_owner_id = attrs.get("owner_id", current_owner_id)

        members_ids = attrs.get("members_ids", None)

        if members_ids is not None and new_owner_id is not None:
            if new_owner_id not in members_ids:
                msg = "Impossible de retirer le responsable de l'équipe des membres."
                raise ValidationError({"members_ids": msg})

        return attrs
