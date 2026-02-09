import pytest
from rest_framework.test import APIClient

from departments.models import Department
from teams.models import Teams
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
def other_user(db):
    return User.objects.create_user(
        email="other@test.com",
        password="password",
        first_name="Other",
        last_name="User",
        role=UserRole.USER,
    )


@pytest.fixture
def department(db):
    return Department.objects.create(
        name="Engineering",
        description="Builds product features",
    )


@pytest.fixture
def other_department(db):
    return Department.objects.create(
        name="Support",
        description="Handles customer support",
    )


@pytest.fixture
def team(db, normal_user, department):
    return Teams.objects.create(
        name="Alpha",
        description="Core platform team",
        owner=normal_user,
        department=department,
    )


@pytest.fixture
def other_team(db, other_user, other_department):
    return Teams.objects.create(
        name="Beta",
        description="Operations team",
        owner=other_user,
        department=other_department,
    )
