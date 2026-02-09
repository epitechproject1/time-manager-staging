import pytest
from django.urls import reverse
from rest_framework import status

from clocks.models import Clock


@pytest.mark.django_db
def test_list_clocks(api_client, user, clock):
    api_client.force_authenticate(user=user)
    response = api_client.get(reverse("clocks-list"))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_create_clock(api_client, user):
    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse("clocks-list"),
        data={
            "user": user.id,
            "work_date": "2026-02-10",
            "clock_in": "09:00:00",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert Clock.objects.count() == 1


@pytest.mark.django_db
def test_retrieve_clock(api_client, user, clock):
    api_client.force_authenticate(user=user)

    response = api_client.get(reverse("clocks-detail", args=[clock.id]))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_update_clock(api_client, user, clock):
    api_client.force_authenticate(user=user)

    response = api_client.patch(
        reverse("clocks-detail", args=[clock.id]),
        data={"clock_out": "18:00:00"},
    )

    assert response.status_code == status.HTTP_200_OK
    clock.refresh_from_db()
    assert clock.clock_out is not None


@pytest.mark.django_db
def test_delete_clock(api_client, user, clock):
    api_client.force_authenticate(user=user)

    response = api_client.delete(reverse("clocks-detail", args=[clock.id]))
    assert response.status_code == status.HTTP_204_NO_CONTENT
