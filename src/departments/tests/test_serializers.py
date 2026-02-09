import pytest

from departments.serializers import DepartmentSerializer


@pytest.mark.django_db
def test_department_serializer_read_only_fields(department):
    serializer = DepartmentSerializer(department)
    data = serializer.data

    assert data["id"] == department.id
    assert data["name"] == department.name
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.django_db
def test_department_serializer_invalid_data(admin_user):
    from departments.serializers import DepartmentSerializer

    # Nom manquant => doit être invalide
    serializer = DepartmentSerializer(data={"description": "Test"})
    assert not serializer.is_valid()
    assert "name" in serializer.errors
