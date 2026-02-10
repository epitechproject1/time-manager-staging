import pytest

from permissions.constants import PermissionType


@pytest.mark.django_db
def test_create_permission(permission):
    assert permission.permission_type == PermissionType.READ
    assert permission.start_date is not None
    assert permission.created_at is not None


@pytest.mark.django_db
def test_permission_str(permission):
    value = str(permission)
    assert "READ" in value
