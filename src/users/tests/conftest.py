import pytest
from rest_framework.test import APIClient

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
