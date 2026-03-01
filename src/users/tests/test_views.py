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
def test_user_search_default_page_size_is_10(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    for idx in range(15):
        User.objects.create_user(
            email=f"user{idx}@test.com",
            password=DEFAULT_PASSWORD,
            first_name=f"User{idx}",
            last_name="Batch",
            phone_number=f"06111111{idx:02d}",
            role=UserRole.USER,
        )

    response = api_client.get(reverse("user-search"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["page_size"] == 10
    assert response.data["total"] >= 15
    assert len(response.data["data"]) == 10


@pytest.mark.django_db
def test_user_search_custom_page_size(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    for idx in range(30):
        User.objects.create_user(
            email=f"limited{idx}@test.com",
            password=DEFAULT_PASSWORD,
            first_name=f"Limited{idx}",
            last_name="Batch",
            phone_number=f"06222222{idx:02d}",
            role=UserRole.USER,
        )

    response = api_client.get(reverse("user-search"), data={"page_size": 5})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["page_size"] == 5
    assert response.data["total"] >= 30
    assert len(response.data["data"]) == 5


@pytest.mark.django_db
def test_user_search_pagination_page_2(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    for idx in range(25):
        User.objects.create_user(
            email=f"page{idx}@test.com",
            password=DEFAULT_PASSWORD,
            first_name=f"Page{idx}",
            last_name="Batch",
            phone_number=f"06333333{idx:02d}",
            role=UserRole.USER,
        )

    response = api_client.get(reverse("user-search"), data={"page_size": 10, "page": 2})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["page"] == 2
    assert response.data["page_size"] == 10
    assert response.data["total"] >= 25
    assert response.data["total_pages"] >= 3
    assert len(response.data["data"]) == 10


@pytest.mark.django_db
def test_user_export_pdf(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    response = api_client.get(reverse("user-export"), data={"file_format": "pdf"})

    assert response.status_code == status.HTTP_200_OK
    assert response["Content-Type"] == "application/pdf"
    assert "users.pdf" in response["Content-Disposition"]


@pytest.mark.django_db
def test_user_export_csv_structured_headers(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    response = api_client.get(reverse("user-export"), data={"file_format": "csv"})

    assert response.status_code == status.HTTP_200_OK
    assert response["Content-Type"].startswith("text/csv")
    assert "users.csv" in response["Content-Disposition"]

    content = response.content.decode("utf-8-sig").splitlines()
    first_line = content[0]
    second_line = content[1]
    assert ";" in first_line
    assert first_line == "sep=;"
    assert "ID;Prenom;Nom;Email" in second_line


@pytest.mark.django_db
def test_user_export_csv_is_sorted_by_id_asc(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    response = api_client.get(reverse("user-export"), data={"file_format": "csv"})

    assert response.status_code == status.HTTP_200_OK
    lines = response.content.decode("utf-8-sig").splitlines()
    data_lines = lines[2:]  # ligne sep + header
    ids = []
    for line in data_lines:
        if not line.strip():
            continue
        first_col = line.split(";")[0].strip()
        if first_col.isdigit():
            ids.append(int(first_col))

    assert ids == sorted(ids)
