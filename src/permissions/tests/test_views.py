import pytest
from django.urls import reverse
from rest_framework import status

from permissions.constants import PermissionType
from permissions.models import Permission


@pytest.mark.django_db
def test_list_permissions_authenticated(api_client, normal_user, permission):
    api_client.force_authenticate(user=normal_user)

    response = api_client.get(reverse("permission-list"))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_create_permission_admin(api_client, admin_user, normal_user):
    api_client.force_authenticate(user=admin_user)

    response = api_client.post(
        reverse("permission-list"),
        data={
            "permission_type": PermissionType.WRITE,
            "start_date": "2026-02-10",
            "granted_to_user": normal_user.id,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert Permission.objects.count() == 1


@pytest.mark.django_db
def test_create_permission_forbidden_for_user(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)

    response = api_client.post(
        reverse("permission-list"),
        data={
            "permission_type": PermissionType.WRITE,
            "start_date": "2026-02-10",
            "granted_to_user": normal_user.id,
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_delete_permission_admin(api_client, admin_user, permission):
    api_client.force_authenticate(user=admin_user)

    response = api_client.delete(reverse("permission-detail", args=[permission.id]))

    assert response.status_code == status.HTTP_204_NO_CONTENT
