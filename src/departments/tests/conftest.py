import pytest
from rest_framework.test import APIClient

from departments.models import Department
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
        is_staff=True,
    )


@pytest.fixture
def normal_user(db):
    return User.objects.create_user(
        email="user@test.com",
        password="password",
        first_name="Normal",
        last_name="User",
    )


@pytest.fixture
def department(db, normal_user):
    return Department.objects.create(
        name="IT", description="IT Department", director=normal_user, is_active=True
    )
