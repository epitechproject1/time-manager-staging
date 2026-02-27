import pytest
from django.urls import reverse
from rest_framework import status

from departments.models import Department
from teams.models import Teams


@pytest.mark.django_db
def test_list_departments_authenticated(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    url = reverse("department-list")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK

    # DRF default list() -> returns a LIST (not {"data": ..., "total": ...})
    assert isinstance(response.data, list)


@pytest.mark.django_db
def test_list_departments_unauthenticated(api_client):
    url = reverse("department-list")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_create_department(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    url = reverse("department-list")
    payload = {"name": "HR", "description": "Human Resources"}

    response = api_client.post(url, data=payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert Department.objects.filter(name="HR").exists()


@pytest.mark.django_db
def test_update_department(api_client, admin_user, department):
    api_client.force_authenticate(user=admin_user)

    url = reverse("department-detail", args=[department.id])
    response = api_client.patch(url, data={"name": "New Name"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    department.refresh_from_db()
    assert department.name == "New Name"


@pytest.mark.django_db
def test_delete_department(api_client, admin_user, department):
    api_client.force_authenticate(user=admin_user)

    url = reverse("department-detail", args=[department.id])
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Department.objects.filter(id=department.id).exists()


@pytest.mark.django_db
def test_delete_department_forbidden_if_has_teams(api_client, admin_user, department):
    api_client.force_authenticate(user=admin_user)

    Teams.objects.create(name="Team A", department=department)

    url = reverse("department-detail", args=[department.id])
    response = api_client.delete(url)

    # perform_destroy -> raises ValidationError -> 400
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Department.objects.filter(id=department.id).exists()


@pytest.mark.django_db
def test_departments_my_departments(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    url = reverse("department-my-departments")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, dict)
    assert "data" in response.data
    assert "total" in response.data


@pytest.mark.django_db
def test_departments_stats(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    url = reverse("department-stats")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "total_departments" in response.data
    assert "total_employees" in response.data
    assert "avg_per_department" in response.data
    assert "this_month_count" in response.data
    assert "timestamp" in response.data
