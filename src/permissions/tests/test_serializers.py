from datetime import timedelta

import pytest
from django.utils import timezone

from permissions.constants import PermissionType
from permissions.serializers import (
    PermissionCreateSerializer,
    PermissionSerializer,
    PermissionUpdateSerializer,
)


@pytest.mark.django_db
def test_permission_serializer(permission):
    serializer = PermissionSerializer(permission)
    data = serializer.data

    assert data["permission_type"] == PermissionType.READ
    assert "granted_by_user" in data
    assert "granted_to_user" in data


@pytest.mark.django_db
def test_permission_create_serializer_valid(admin_user, normal_user):
    future_date = timezone.now().date() + timedelta(days=1)

    serializer = PermissionCreateSerializer(
        data={
            "permission_type": PermissionType.WRITE,
            "start_date": future_date,
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
            "permission_type": PermissionType.WRITE,
            "start_date": "2026-02-10",
            "end_date": "2026-02-01",
            "granted_to_user": normal_user.id,
        },
        context={"request": type("obj", (), {"user": admin_user})()},
    )

    assert serializer.is_valid() is False


@pytest.mark.django_db
def test_permission_update_serializer(permission):
    serializer = PermissionUpdateSerializer(
        permission,
        data={"permission_type": PermissionType.ADMIN},
        partial=True,
    )

    assert serializer.is_valid(), serializer.errors
    permission = serializer.save()

    assert permission.permission_type == PermissionType.ADMIN
