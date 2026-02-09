import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_list_teams(api_client, normal_user, team, other_team):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-list")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2


@pytest.mark.django_db
def test_filter_teams_by_department(api_client, normal_user, department, team):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-list")
    response = api_client.get(url, {"department": department.id})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["name"] == "Alpha"


@pytest.mark.django_db
def test_filter_teams_by_owner(api_client, normal_user, team):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-list")
    response = api_client.get(url, {"owner": normal_user.id})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["name"] == "Alpha"


@pytest.mark.django_db
def test_my_teams_action(api_client, normal_user, team):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-my-teams")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["owner"] == normal_user.id


@pytest.mark.django_db
def test_create_team(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-list")
    payload = {
        "name": "New Team",
        "description": "Created by test",
    }

    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "New Team"
    assert response.data["owner"] == normal_user.id


@pytest.mark.django_db
def test_update_team(api_client, normal_user, team, department):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-detail", args=[team.id])
    payload = {
        "name": "Updated Team",
        "description": "Updated description",
        "owner": normal_user.id,
        "department": department.id,
    }

    response = api_client.put(url, payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "Updated Team"


@pytest.mark.django_db
def test_delete_team(api_client, normal_user, team):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-detail", args=[team.id])
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
