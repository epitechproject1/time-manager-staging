import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_list_teams(api_client, normal_user, team, other_team):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-list")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "data" in response.data
    assert "total" in response.data
    assert response.data["total"] == 2
    assert len(response.data["data"]) == 2

    first = response.data["data"][0]
    assert "owner" in first
    assert (first["owner"] is None) or isinstance(first["owner"], dict)
    assert "department" in first
    assert (first["department"] is None) or isinstance(first["department"], dict)
    assert "members_count" in first


@pytest.mark.django_db
def test_filter_teams_by_department(api_client, normal_user, department, team):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-list")
    response = api_client.get(url, {"department_id": department.id})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["total"] == 1
    assert len(response.data["data"]) == 1
    assert response.data["data"][0]["name"] == team.name


@pytest.mark.django_db
def test_filter_teams_by_owner(api_client, normal_user, team):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-list")
    response = api_client.get(url, {"owner_id": normal_user.id})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["total"] == 1
    assert len(response.data["data"]) == 1
    assert response.data["data"][0]["name"] == team.name


@pytest.mark.django_db
def test_my_teams_action(api_client, normal_user, team):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-my-teams")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "data" in response.data
    assert "total" in response.data
    assert response.data["total"] == 1
    assert len(response.data["data"]) == 1
    assert response.data["data"][0]["owner"]["id"] == normal_user.id


@pytest.mark.django_db
def test_create_team(api_client, admin_user, department):
    api_client.force_authenticate(user=admin_user)

    url = reverse("teams-list")
    payload = {
        "name": "New Team",
        "description": "Created by test",
        "department_id": department.id,
    }

    response = api_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["name"] == "New Team"
    assert response.data["department"]["id"] == department.id

    if "members" in response.data:
        assert isinstance(response.data["members"], list)
    else:
        assert "members_count" in response.data


@pytest.mark.django_db
def test_create_team_forbidden_for_normal_user(api_client, normal_user, department):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-list")
    payload = {
        "name": "New Team",
        "description": "Created by test",
        "department_id": department.id,
    }

    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_update_team(api_client, admin_user, team, department):
    api_client.force_authenticate(user=admin_user)

    url = reverse("teams-detail", args=[team.id])
    payload = {
        "name": "Updated Team",
        "description": "Updated description",
        "owner_id": admin_user.id,
        "department_id": department.id,
        "members_ids": [admin_user.id],
    }

    response = api_client.put(url, payload, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["name"] == "Updated Team"
    assert response.data["department"]["id"] == department.id
    assert response.data["owner"]["id"] == admin_user.id


@pytest.mark.django_db
def test_update_team_forbidden_for_normal_user(
    api_client, normal_user, team, department
):
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
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_delete_team(api_client, admin_user, team):
    api_client.force_authenticate(user=admin_user)

    url = reverse("teams-detail", args=[team.id])
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_delete_team_forbidden_for_normal_user(api_client, normal_user, team):
    api_client.force_authenticate(user=normal_user)

    url = reverse("teams-detail", args=[team.id])
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN
