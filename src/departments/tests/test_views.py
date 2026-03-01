import pytest
from django.urls import reverse
from rest_framework import status

from departments.models import Department
from teams.models import Teams
from users.constants import UserRole


def make_team(*, name: str, department: Department, owner=None):
    """
    Crée une team en restant compatible avec ton modèle Teams
    (description/owner peuvent être requis selon ton modèle).
    """
    kwargs = {"name": name, "department": department}

    if hasattr(Teams, "description"):
        kwargs["description"] = "desc"

    if hasattr(Teams, "owner"):
        kwargs["owner"] = owner

    try:
        return Teams.objects.create(**kwargs)
    except Exception:

        if owner is None and hasattr(Teams, "owner"):
            raise
        raise


def make_manager_user(django_user_model):
    """
    Crée un user role=MANAGER sans dépendre d'une fixture.
    Adapte les champs requis (email/username/password) selon ton User model.
    """
    data = {
        "email": "manager@test.com",
        "first_name": "Manager",
        "last_name": "User",
        "role": UserRole.MANAGER,
    }

    if "username" in [f.name for f in django_user_model._meta.fields]:
        data["username"] = "manager"

    user = django_user_model.objects.create(**data)
    user.set_password("pass1234")
    user.save()
    return user


@pytest.mark.django_db
def test_list_departments_authenticated(api_client, admin_user, department):
    api_client.force_authenticate(user=admin_user)

    url = reverse("department-list")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) >= 1


@pytest.mark.django_db
def test_list_departments_unauthenticated(api_client):
    url = reverse("department-list")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_create_department(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    url = reverse("department-list")
    payload = {"name": "HR", "description": "Human Resources"}

    response = api_client.post(url, data=payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert Department.objects.filter(name="HR").exists()


@pytest.mark.django_db
def test_create_department_forbidden_for_normal_user(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)

    url = reverse("department-list")
    payload = {"name": "HR2", "description": "Human Resources"}

    response = api_client.post(url, data=payload, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_update_department(api_client, admin_user, department):
    api_client.force_authenticate(user=admin_user)

    url = reverse("department-detail", args=[department.id])
    response = api_client.patch(url, data={"name": "New Name"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    department.refresh_from_db()
    assert department.name == "New Name"


@pytest.mark.django_db
def test_delete_department(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)

    dept = Department.objects.create(name="DeptDelete")
    url = reverse("department-detail", args=[dept.id])

    response = api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Department.objects.filter(id=dept.id).exists()


@pytest.mark.django_db
def test_delete_department_forbidden_if_has_teams(api_client, admin_user, department):
    api_client.force_authenticate(user=admin_user)

    make_team(
        name="Team A",
        department=department,
        owner=getattr(admin_user, "pk", None) and admin_user,
    )

    url = reverse("department-detail", args=[department.id])
    response = api_client.delete(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Department.objects.filter(id=department.id).exists()


@pytest.mark.django_db
def test_departments_my_departments(api_client, admin_user, department):
    api_client.force_authenticate(user=admin_user)

    department.director = admin_user
    department.save(update_fields=["director"])

    url = reverse("department-my-departments")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, dict)
    assert "data" in response.data
    assert "total" in response.data
    assert response.data["total"] >= 1


@pytest.mark.django_db
def test_departments_stats_admin(api_client, admin_user, department):
    api_client.force_authenticate(user=admin_user)

    url = reverse("department-stats")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "total_departments" in response.data
    assert "total_employees" in response.data
    assert "avg_per_department" in response.data
    assert "this_month_count" in response.data
    assert "timestamp" in response.data


@pytest.mark.django_db
def test_departments_stats_forbidden_for_normal_user(api_client, normal_user):
    api_client.force_authenticate(user=normal_user)

    url = reverse("department-stats")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


# -------------------------
# ✅ stats-breakdown tests
# -------------------------


@pytest.mark.django_db
def test_departments_stats_breakdown_admin(api_client, admin_user, department):
    api_client.force_authenticate(user=admin_user)

    url = reverse("department-stats-breakdown")
    res = api_client.get(url)

    assert res.status_code == status.HTTP_200_OK
    assert isinstance(res.data, list)
    assert len(res.data) >= 1
    row = res.data[0]
    assert {"id", "name", "teams_count", "members_count"} <= set(row.keys())


@pytest.mark.django_db
def test_departments_stats_breakdown_manager_scoped(
    api_client, django_user_model, admin_user
):
    """
    manager => uniquement les départements où il est owner d'au moins une team
    """
    manager = make_manager_user(django_user_model)
    api_client.force_authenticate(user=manager)

    dept_a = Department.objects.create(name="DeptA")
    dept_b = Department.objects.create(name="DeptB")

    make_team(name="TeamOwned", department=dept_a, owner=manager)
    make_team(name="TeamNotOwned", department=dept_b, owner=admin_user)

    url = reverse("department-stats-breakdown")
    res = api_client.get(url)

    assert res.status_code == status.HTTP_200_OK
    ids = [r["id"] for r in res.data]
    assert dept_a.id in ids
    assert dept_b.id not in ids


@pytest.mark.django_db
def test_departments_stats_breakdown_user_scoped_as_member(
    api_client, normal_user, admin_user
):
    """
    user => uniquement departments où il est membre d'au moins une team
    """
    api_client.force_authenticate(user=normal_user)

    dept_a = Department.objects.create(name="DeptA2")
    dept_b = Department.objects.create(name="DeptB2")

    team_a = make_team(name="TeamA2", department=dept_a, owner=admin_user)
    team_b = make_team(name="TeamB2", department=dept_b, owner=admin_user)

    team_a.members.add(normal_user)
    team_b.members.clear()

    url = reverse("department-stats-breakdown")
    res = api_client.get(url)

    assert res.status_code == status.HTTP_200_OK
    ids = [r["id"] for r in res.data]
    assert dept_a.id in ids
    assert dept_b.id not in ids


@pytest.mark.django_db
def test_departments_stats_breakdown_forbidden_when_no_access(
    api_client, normal_user, admin_user
):
    """
    user sans être membre d'aucune team => 403 ("Aucun département accessible.")
    """
    api_client.force_authenticate(user=normal_user)

    dept = Department.objects.create(name="DeptNoAccess")
    team = make_team(name="TeamNoAccess", department=dept, owner=admin_user)
    team.members.clear()

    url = reverse("department-stats-breakdown")
    res = api_client.get(url)

    assert res.status_code == status.HTTP_403_FORBIDDEN
