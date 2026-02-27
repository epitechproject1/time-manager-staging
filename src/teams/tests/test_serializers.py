import pytest
from django.contrib.auth import get_user_model
from django.db.models import Count

from teams.models import Teams
from teams.serializers import TeamsSerializer

User = get_user_model()


@pytest.mark.django_db
def test_team_serializer_fields(team, normal_user):
    team.members.add(normal_user)

    team_annotated = (
        Teams.objects.filter(pk=team.pk)
        .select_related("owner", "department")
        .prefetch_related("members")
        .annotate(members_count=Count("members", distinct=True))
        .get()
    )

    serializer = TeamsSerializer(team_annotated)
    data = serializer.data

    assert data["id"] == team.id
    assert data["name"] == team.name
    assert data["description"] == team.description

    assert isinstance(data["owner"], dict)
    assert data["owner"]["id"] == team.owner.id

    if team.department is not None:
        assert isinstance(data["department"], dict)
        assert data["department"]["id"] == team.department.id
        assert data["department"]["name"] == team.department.name
    else:
        assert data["department"] is None

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

    team_annotated = (
        Teams.objects.filter(pk=team.pk)
        .annotate(members_count=Count("members", distinct=True))
        .get()
    )

    serializer = TeamsSerializer(team_annotated)
    data = serializer.data

    assert data["owner"] is None
    assert data["department"] is None

    assert data["members"] == []
    assert data["members_count"] == 0

    assert "members_ids" not in data
    assert "owner_id" not in data
    assert "department_id" not in data
