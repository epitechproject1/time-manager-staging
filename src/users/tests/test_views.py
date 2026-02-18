import pytest
from django.urls import reverse
from rest_framework import status

from users.constants import UserRole
from users.models import User

DEFAULT_PASSWORD = "StrongPass123!"


# =========================
# LIST
# =========================


@pytest.mark.django_db
def test_list_users_forbidden_for_normal_user(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)

    response = api_client.get(reverse("user-list"))

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_list_users_allowed_for_admin(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    response = api_client.get(reverse("user-list"))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_list_users_unauthenticated(api_client):
    response = api_client.get(reverse("user-list"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================
# CREATE
# =========================


@pytest.mark.django_db
def test_create_user_admin(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    response = api_client.post(
        reverse("user-list"),
        data={
            "email": "created@test.com",
            "first_name": "Created",
            "last_name": "User",
            "phone_number": "0600000000",
            "role": UserRole.USER,
            "password": DEFAULT_PASSWORD,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(email="created@test.com").exists()


@pytest.mark.django_db
def test_create_user_forbidden_for_non_admin(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)

    response = api_client.post(
        reverse("user-list"),
        data={
            "email": "forbidden@test.com",
            "first_name": "No",
            "last_name": "Access",
            "phone_number": "0600000000",
            "role": UserRole.USER,
            "password": DEFAULT_PASSWORD,
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


# =========================
# RETRIEVE
# =========================


@pytest.mark.django_db
def test_user_can_retrieve_own_profile(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)

    response = api_client.get(reverse("user-detail", args=[normal_user.id]))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_user_cannot_retrieve_other_profile(api_client, normal_user, admin_user):
    api_client.force_authenticate(user=normal_user)

    response = api_client.get(reverse("user-detail", args=[admin_user.id]))

    assert response.status_code == status.HTTP_404_NOT_FOUND


# =========================
# UPDATE
# =========================


@pytest.mark.django_db
def test_user_can_update_self(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)

    response = api_client.patch(
        reverse("user-detail", args=[normal_user.id]),
        data={"first_name": "Updated"},
    )

    assert response.status_code == status.HTTP_200_OK

    normal_user.refresh_from_db()
    assert normal_user.first_name == "Updated"


@pytest.mark.django_db
def test_admin_can_update_any_user(api_client, admin_user, normal_user):
    api_client.force_authenticate(user=admin_user)

    response = api_client.patch(
        reverse("user-detail", args=[normal_user.id]),
        data={"first_name": "Updated"},
    )

    assert response.status_code == status.HTTP_200_OK


# =========================
# DELETE
# =========================


@pytest.mark.django_db
def test_user_can_delete_self(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)

    response = api_client.delete(reverse("user-detail", args=[normal_user.id]))

    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_admin_can_delete_user(api_client, admin_user, normal_user):
    api_client.force_authenticate(user=admin_user)

    response = api_client.delete(reverse("user-detail", args=[normal_user.id]))

    assert response.status_code == status.HTTP_204_NO_CONTENT


# =========================
# SEARCH / EXPORT
# =========================


@pytest.mark.django_db
def test_user_search_with_filters(api_client, admin_user, normal_user):
    api_client.force_authenticate(user=admin_user)

    User.objects.create_user(
        email="manager@test.com",
        password=DEFAULT_PASSWORD,
        first_name="Manage",
        last_name="R",
        phone_number="0700000000",
        role=UserRole.MANAGER,
        is_active=False,
    )

    response = api_client.get(
        reverse("user-search"),
        data={
            "q": "man",
            "role": UserRole.MANAGER,
            "is_active": "false",
            "ordering": "email",
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["total"] == 1
    assert response.data["data"][0]["email"] == "manager@test.com"


@pytest.mark.django_db
def test_user_export_pdf(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    response = api_client.get(reverse("user-export"), data={"file_format": "pdf"})

    assert response.status_code == status.HTTP_200_OK
    assert response["Content-Type"] == "application/pdf"
    assert "users.pdf" in response["Content-Disposition"]
