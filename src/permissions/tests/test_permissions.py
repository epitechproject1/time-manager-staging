import pytest
from rest_framework.test import APIRequestFactory

from permissions.permissions import IsAdminOrPermissionManager


@pytest.mark.django_db
def test_safe_methods_allowed_for_authenticated(normal_user):
    factory = APIRequestFactory()
    request = factory.get("/permissions/")
    request.user = normal_user

    permission = IsAdminOrPermissionManager()
    assert permission.has_permission(request, None) is True


@pytest.mark.django_db
def test_write_denied_for_non_admin(normal_user):
    factory = APIRequestFactory()
    request = factory.post("/permissions/")
    request.user = normal_user

    permission = IsAdminOrPermissionManager()
    assert permission.has_permission(request, None) is False
