from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from permissions.constants import PermissionType
from permissions.models import Permission


def choice_value(choice):
    return getattr(choice, "value", choice)


@pytest.mark.django_db
def test_list_permissions_authenticated(api_client, normal_user, permission):
    api_client.force_authenticate(user=normal_user)

    response = api_client.get(reverse("permission-list"))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_create_permission_admin(api_client, admin_user, normal_user):
    api_client.force_authenticate(user=admin_user)

    start_date = (timezone.now().date() + timedelta(days=1)).isoformat()

    response = api_client.post(
        reverse("permission-list"),
        data={
            "permission_type": choice_value(PermissionType.WRITE),
            "start_date": start_date,
            "granted_to_user": normal_user.id,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert Permission.objects.count() == 1


@pytest.mark.django_db
def test_create_permission_forbidden_for_user(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)

    start_date = (timezone.now().date() + timedelta(days=1)).isoformat()

    response = api_client.post(
        reverse("permission-list"),
        data={
            "permission_type": choice_value(PermissionType.WRITE),
            "start_date": start_date,
            "granted_to_user": normal_user.id,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN, response.data


@pytest.mark.django_db
def test_delete_permission_admin(api_client, admin_user, permission):
    api_client.force_authenticate(user=admin_user)

    response = api_client.delete(reverse("permission-detail", args=[permission.id]))

    assert response.status_code == status.HTTP_204_NO_CONTENT
