import pytest
from django.urls import reverse
from rest_framework import status
from departments.models import Department

@pytest.mark.django_db
def test_list_departments_authenticated(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    url = reverse("department-list")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_list_departments_unauthenticated(api_client):
    url = reverse("department-list")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
def test_create_department(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    url = reverse("department-list")
    data = {"name": "HR", "description": "Human Resources"}
    response = api_client.post(url, data=data)
    assert response.status_code == status.HTTP_201_CREATED
    assert Department.objects.filter(name="HR").exists()

@pytest.mark.django_db
def test_update_department(api_client, admin_user, department):
    api_client.force_authenticate(user=admin_user)
    url = reverse("department-detail", args=[department.id])
    response = api_client.patch(url, data={"name": "New Name"})
    assert response.status_code == status.HTTP_200_OK
    department.refresh_from_db()
    assert department.name == "New Name"

@pytest.mark.django_db
def test_delete_department(api_client, admin_user, department):
    api_client.force_authenticate(user=admin_user)
    url = reverse("department-detail", args=[department.id])
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
