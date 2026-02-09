import pytest

from teams.models import Teams


@pytest.mark.django_db
def test_team_creation(team, normal_user, department):
    assert team.name == "Alpha"
    assert team.description == "Core platform team"
    assert team.owner == normal_user
    assert team.department == department


@pytest.mark.django_db
def test_team_str_method(team):
    assert str(team) == "Alpha: Core platform team"


@pytest.mark.django_db
def test_team_timestamps(team):
    assert team.created_at is not None
    assert team.updated_at is not None


@pytest.mark.django_db
def test_team_owner_can_be_null():
    team = Teams.objects.create(
        name="No Owner Team",
        description="Team without owner",
    )
    assert team.owner is None


@pytest.mark.django_db
def test_team_department_can_be_null():
    team = Teams.objects.create(
        name="No Department Team",
        description="Team without department",
    )
    assert team.department is None
