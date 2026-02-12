import pytest
from django.contrib.auth import get_user_model

from teams.models import Teams
from teams.serializers import TeamsSerializer

User = get_user_model()


@pytest.mark.django_db
def test_team_serializer_fields(team, normal_user, department):
    team.members.add(normal_user)

    serializer = TeamsSerializer(team)
    data = serializer.data

    assert data["id"] == team.id
    assert data["name"] == team.name
    assert data["description"] == team.description

    assert isinstance(data["owner"], dict)
    assert data["owner"]["id"] == normal_user.id
    assert data["owner"]["email"] == normal_user.email
    assert data["owner"]["first_name"] == normal_user.first_name
    assert data["owner"]["last_name"] == normal_user.last_name

    assert isinstance(data["department"], dict)
    assert data["department"]["id"] == department.id
    assert data["department"]["name"] == department.name

    assert "members" in data
    assert isinstance(data["members"], list)
    assert any(m["id"] == normal_user.id for m in data["members"])

    assert data["members_count"] == team.members.count()

    assert "members_ids" not in data
    assert "owner_id" not in data
    assert "department_id" not in data

    assert data["created_at"] is not None
    assert data["updated_at"] is not None


@pytest.mark.django_db
def test_serializer_without_owner_and_department():
    team = Teams.objects.create(
        name="No Owner Team",
        description="Team without owner and department",
        owner=None,
        department=None,
    )
    serializer = TeamsSerializer(team)
    data = serializer.data

    assert data["owner"] is None
    assert data["department"] is None

    assert data["members"] == []
    assert data["members_count"] == 0

    assert "members_ids" not in data
    assert "owner_id" not in data
    assert "department_id" not in data
