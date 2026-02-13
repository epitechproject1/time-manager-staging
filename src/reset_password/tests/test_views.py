import pytest
from django.urls import reverse
from rest_framework import status

from reset_password.models import PasswordResetCode


# =========================
# REQUEST RESET
# =========================
@pytest.mark.django_db
def test_password_reset_request_existing_email(api_client, normal_user):
    response = api_client.post(
        reverse("password_reset_request"),
        data={"email": normal_user.email},
    )

    assert response.status_code == status.HTTP_200_OK
    assert PasswordResetCode.objects.filter(user=normal_user).exists()


@pytest.mark.django_db
def test_password_reset_request_unknown_email(api_client):
    response = api_client.post(
        reverse("password_reset_request"),
        data={"email": "unknown@test.com"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert PasswordResetCode.objects.count() == 0


# =========================
# VERIFY CODE
# =========================
@pytest.mark.django_db
def test_password_reset_verify_valid(api_client, normal_user):
    PasswordResetCode.objects.create(
        user=normal_user,
        code="123456",
        expires_at=PasswordResetCode.generate_expiration(),
    )

    response = api_client.post(
        reverse("password_reset_verify"),
        data={
            "email": normal_user.email,
            "code": "123456",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["valid"] is True


@pytest.mark.django_db
def test_password_reset_verify_invalid(api_client, normal_user):
    response = api_client.post(
        reverse("password_reset_verify"),
        data={
            "email": normal_user.email,
            "code": "000000",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["valid"] is False


# =========================
# CONFIRM RESET
# =========================
@pytest.mark.django_db
def test_password_reset_confirm_success(api_client, normal_user):
    PasswordResetCode.objects.create(
        user=normal_user,
        code="654321",
        expires_at=PasswordResetCode.generate_expiration(),
    )

    response = api_client.post(
        reverse("password_reset_confirm"),
        data={
            "email": normal_user.email,
            "code": "654321",
            "new_password": "NewStrongPass123!",
        },
    )

    assert response.status_code == status.HTTP_200_OK

    normal_user.refresh_from_db()
    assert normal_user.check_password("NewStrongPass123!")


@pytest.mark.django_db
def test_password_reset_confirm_invalid_code(api_client, normal_user):
    response = api_client.post(
        reverse("password_reset_confirm"),
        data={
            "email": normal_user.email,
            "code": "999999",
            "new_password": "NewStrongPass123!",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
