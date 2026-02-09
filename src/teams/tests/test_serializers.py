import pytest
from teams.serializers import TeamsSerializer
from teams.models import Teams


@pytest.mark.django_db
def test_team_serializer_fields(team, normal_user, department):
    serializer = TeamsSerializer(team)
    data = serializer.data

    assert data["id"] == team.id
    assert data["name"] == team.name
    assert data["description"] == team.description
    assert data["owner"] == normal_user.id
    assert data["department"] == department.id

    assert data["owner_name"] == "Normal User"
    assert data["owner_email"] == "user@test.com"
    assert data["department_name"] == "Engineering"

    assert data["created_at"] is not None
    assert data["updated_at"] is not None


@pytest.mark.django_db
def test_serializer_without_owner_and_department():
    team = Teams.objects.create(
        name="No Owner Team",
        description="Team without owner and department",
    )
    serializer = TeamsSerializer(team)
    data = serializer.data

    assert data["owner"] is None
    assert data["owner_name"] is None
    assert data["owner_email"] is None
    assert data["department"] is None
    assert data["department_name"] is None
