import pytest
from rest_framework.test import APIRequestFactory

from users.permissions import IsAdminForCreateOtherwiseReadOnly


@pytest.mark.django_db
def test_permission_read_authenticated(normal_user):
    factory = APIRequestFactory()
    request = factory.get("/users/")
    request.user = normal_user

    permission = IsAdminForCreateOtherwiseReadOnly()
    assert permission.has_permission(request, None) is True


@pytest.mark.django_db
def test_permission_create_admin(admin_user):
    factory = APIRequestFactory()
    request = factory.post("/users/")
    request.user = admin_user

    permission = IsAdminForCreateOtherwiseReadOnly()
    assert permission.has_permission(request, None) is True


@pytest.mark.django_db
def test_permission_create_non_admin(normal_user):
    factory = APIRequestFactory()
    request = factory.post("/users/")
    request.user = normal_user

    permission = IsAdminForCreateOtherwiseReadOnly()
    assert permission.has_permission(request, None) is False
