import pytest


@pytest.mark.django_db
def test_create_department(department):
    assert department.name == "IT"
    assert department.description == "IT Department"
    assert department.director is not None
    assert department.is_active is True


@pytest.mark.django_db
def test_department_str(department):
    assert str(department) == department.name
