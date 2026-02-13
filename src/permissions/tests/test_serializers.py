from datetime import timedelta

import pytest
from django.utils import timezone

from permissions.constants import PermissionType
from permissions.serializers import (
    PermissionCreateSerializer,
    PermissionSerializer,
    PermissionUpdateSerializer,
)


def choice_value(choice):
    return getattr(choice, "value", choice)


@pytest.mark.django_db
def test_permission_serializer(permission):
    serializer = PermissionSerializer(permission)
    data = serializer.data

    assert data["permission_type"] == choice_value(PermissionType.READ)
    assert "granted_by_user" in data
    assert "granted_to_user" in data


@pytest.mark.django_db
def test_permission_create_serializer_valid(admin_user, normal_user):
    future_date = timezone.now().date() + timedelta(days=1)

    serializer = PermissionCreateSerializer(
        data={
<<<<<<< feature_planning
            "permission_type": choice_value(PermissionType.WRITE),
            "start_date": timezone.now().date() + timedelta(days=1),
=======
            "permission_type": PermissionType.WRITE,
            "start_date": future_date,
>>>>>>> develop
            "granted_to_user": normal_user.id,
        },
        context={"request": type("obj", (), {"user": admin_user})()},
    )

    assert serializer.is_valid(), serializer.errors
    permission = serializer.save()

    assert permission.granted_by_user == admin_user


@pytest.mark.django_db
def test_permission_create_serializer_invalid_dates(admin_user, normal_user):
    serializer = PermissionCreateSerializer(
        data={
            "permission_type": choice_value(PermissionType.WRITE),
            "start_date": (timezone.now().date() + timedelta(days=2)).isoformat(),
            "end_date": (timezone.now().date() + timedelta(days=1)).isoformat(),
            "granted_to_user": normal_user.id,
        },
        context={"request": type("obj", (), {"user": admin_user})()},
    )

    assert serializer.is_valid() is False


@pytest.mark.django_db
def test_permission_update_serializer(permission):
    future_start = timezone.now().date() + timedelta(days=1)

    serializer = PermissionUpdateSerializer(
        permission,
        data={
            "permission_type": choice_value(PermissionType.ADMIN),
            "start_date": future_start,
        },
        partial=True,
    )

    assert serializer.is_valid(), serializer.errors
    permission = serializer.save()

    assert permission.permission_type == choice_value(PermissionType.ADMIN)
