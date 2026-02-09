import pytest
from rest_framework.test import APIClient

from users.constants import UserRole


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(django_user_model):
    return django_user_model.objects.create_user(
        email="admin@test.com",
        password="Admin123!",
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
    )


@pytest.fixture
def normal_user(django_user_model):
    return django_user_model.objects.create_user(
        email="user@test.com",
        password="User123!",
        first_name="Normal",
        last_name="User",
        role=UserRole.USER,
    )
