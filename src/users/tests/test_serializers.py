import pytest

from users.constants import UserRole
from users.models import User
from users.serializers import UserCreateSerializer, UserSerializer, UserUpdateSerializer


@pytest.mark.django_db
def test_user_serializer_read_only_fields(normal_user):
    serializer = UserSerializer(normal_user)
    data = serializer.data

    assert data["email"] == normal_user.email
    assert "created_at" in data
    assert "updated_at" in data
    assert data["role"] == normal_user.role


@pytest.mark.django_db
def test_user_create_serializer_success():
    serializer = UserCreateSerializer(
        data={
            "email": "new@test.com",
            "first_name": "New",
            "last_name": "User",
            "phone_number": "0600000000",
            "role": UserRole.USER,
            "password": "StrongPass123!",
        }
    )

    assert serializer.is_valid(), serializer.errors
    user = serializer.save()

    assert user.email == "new@test.com"
    assert user.check_password("StrongPass123!")  # 🔐 Vérifie le hash


@pytest.mark.django_db
def test_user_create_serializer_duplicate_email(normal_user):
    serializer = UserCreateSerializer(
        data={
            "email": normal_user.email,
            "first_name": "Test",
            "last_name": "User",
            "phone_number": "0600000000",
            "role": UserRole.USER,
            "password": "StrongPass123!",
        }
    )

    assert serializer.is_valid() is False
    assert "email" in serializer.errors


@pytest.mark.django_db
def test_user_create_serializer_password_required():
    serializer = UserCreateSerializer(
        data={
            "email": "nopassword@test.com",
            "first_name": "No",
            "last_name": "Password",
            "phone_number": "0600000000",
            "role": UserRole.USER,
        }
    )

    assert serializer.is_valid() is False
    assert "password" in serializer.errors


@pytest.mark.django_db
def test_user_update_serializer():
    user = User.objects.create_user(
        email="update@test.com",
        password="password",
        first_name="Old",
        last_name="Name",
    )

    serializer = UserUpdateSerializer(
        user,
        data={"first_name": "New"},
        partial=True,
    )

    assert serializer.is_valid(), serializer.errors
    user = serializer.save()

    assert user.first_name == "New"
