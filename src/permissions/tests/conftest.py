from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from permissions.constants import PermissionType
from permissions.models import Permission
from users.constants import UserRole
from users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@test.com",
        password="password",
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        is_staff=True,
    )


@pytest.fixture
def normal_user(db):
    return User.objects.create_user(
        email="user@test.com",
        password="password",
        first_name="Normal",
        last_name="User",
        role=UserRole.USER,
    )


@pytest.fixture
def permission(db, admin_user, normal_user):
    future_date = timezone.now().date() + timedelta(days=1)

    return Permission.objects.create(
        permission_type=PermissionType.READ,
        start_date=future_date,
        granted_by_user=admin_user,
        granted_to_user=normal_user,
    )
