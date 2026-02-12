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

    assert "owner" in response.data[0]
    assert (response.data[0]["owner"] is None) or isinstance(
        response.data[0]["owner"], dict
    )

    assert "department" in response.data[0]
    assert (response.data[0]["department"] is None) or isinstance(
        response.data[0]["department"], dict
    )

    assert "members_count" in response.data[0]


@pytest.mark.django_db
def test_filter_teams_by_department(api_client, normal_user, department, team):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-list")
    response = api_client.get(url, {"department_id": department.id})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["name"] == team.name


@pytest.mark.django_db
def test_filter_teams_by_owner(api_client, normal_user, team):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-list")
    response = api_client.get(url, {"owner_id": normal_user.id})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["name"] == team.name


@pytest.mark.django_db
def test_my_teams_action(api_client, normal_user, team):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-my-teams")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1

    assert response.data[0]["owner"]["id"] == normal_user.id


@pytest.mark.django_db
def test_create_team(api_client, normal_user, department):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-list")
    payload = {
        "name": "New Team",
        "description": "Created by test",
        "department_id": department.id,
    }

    response = api_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "New Team"

    assert response.data["owner"]["id"] == normal_user.id
    assert response.data["department"]["id"] == department.id

    assert any(m["id"] == normal_user.id for m in response.data["members"])


@pytest.mark.django_db
def test_update_team(api_client, normal_user, team, department):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-detail", args=[team.id])
    payload = {
        "name": "Updated Team",
        "description": "Updated description",
        "owner_id": normal_user.id,
        "department_id": department.id,
        "members_ids": [normal_user.id],
    }

    response = api_client.put(url, payload, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "Updated Team"
    assert response.data["department"]["id"] == department.id
    assert response.data["owner"]["id"] == normal_user.id


@pytest.mark.django_db
def test_delete_team(api_client, normal_user, team):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-detail", args=[team.id])
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
