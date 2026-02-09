import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from plannings.models import Planning


@pytest.mark.django_db
def test_list_plannings_unauthenticated(api_client):
    res = api_client.get(reverse("planning-list"))
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_list_plannings_authenticated_only_own(api_client, normal_user, planning_owned_by_normal_user, planning_owned_by_admin):
    api_client.force_authenticate(user=normal_user)

    res = api_client.get(reverse("planning-list"))
    assert res.status_code == status.HTTP_200_OK

    # normal_user doit voir uniquement ses plannings
    ids = [p["id"] for p in res.json()]
    assert planning_owned_by_normal_user.id in ids
    assert planning_owned_by_admin.id not in ids


@pytest.mark.django_db
def test_create_planning_user_creates_for_self(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)

    res = api_client.post(
        reverse("planning-list"),
        data={
            "title": "Created by user",
            "start_datetime": timezone.now().isoformat(),
            "end_datetime": (timezone.now() + timedelta(hours=1)).isoformat(),
            "user": normal_user.id,  # ok
            "planning_type": "SHIFT",
            "work_mode": "REMOTE",
        },
        format="json",
    )
    assert res.status_code == status.HTTP_201_CREATED
    assert Planning.objects.filter(title="Created by user", user=normal_user).exists()


@pytest.mark.django_db
def test_create_planning_user_cannot_create_for_other(api_client, normal_user, admin_user):
    api_client.force_authenticate(user=normal_user)

    res = api_client.post(
        reverse("planning-list"),
        data={
            "title": "Forbidden",
            "start_datetime": timezone.now().isoformat(),
            "end_datetime": (timezone.now() + timedelta(hours=1)).isoformat(),
            "user": admin_user.id,  # interdit
            "planning_type": "SHIFT",
            "work_mode": "REMOTE",
        },
        format="json",
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_planning_forbidden_if_not_owner(api_client, normal_user, planning_owned_by_admin):
    api_client.force_authenticate(user=normal_user)

    res = api_client.patch(
        reverse("planning-detail", args=[planning_owned_by_admin.id]),
        data={"title": "Hack"},
        format="json",
    )
    assert res.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)


@pytest.mark.django_db
def test_invalid_dates_rejected(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)

    now = timezone.now()
    res = api_client.post(
        reverse("planning-list"),
        data={
            "title": "Bad dates",
            "start_datetime": now.isoformat(),
            "end_datetime": (now - timedelta(hours=1)).isoformat(),
            "user": normal_user.id,
            "planning_type": "SHIFT",
            "work_mode": "ONSITE",
        },
        format="json",
    )
    assert res.status_code == status.HTTP_400_BAD_REQUEST
