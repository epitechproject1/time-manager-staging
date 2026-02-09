import pytest

from users.constants import UserRole
from users.models import User


@pytest.mark.django_db
def test_create_user():
    user = User.objects.create_user(
        email="test@test.com",
        password="password",
        first_name="John",
        last_name="Doe",
    )

    assert user.email == "test@test.com"
    assert user.check_password("password")
    assert user.role == UserRole.USER


@pytest.mark.django_db
def test_create_superuser():
    admin = User.objects.create_superuser(
        email="admin@test.com",
        password="password",
        first_name="Admin",
        last_name="User",
    )

    assert admin.is_staff is True
    assert admin.is_superuser is True
    assert admin.role == UserRole.ADMIN
