from types import SimpleNamespace

import pytest
from rest_framework.test import APIRequestFactory

from users.permissions import IsAdminOrOwnerProfile


@pytest.mark.django_db
def test_permission_list_forbidden_for_normal_user(normal_user):
    factory = APIRequestFactory()
    request = factory.get("/users/")
    request.user = normal_user

    view = SimpleNamespace(action="list")

    permission = IsAdminOrOwnerProfile()
    assert permission.has_permission(request, view) is False


@pytest.mark.django_db
def test_permission_list_allowed_for_admin(admin_user):
    factory = APIRequestFactory()
    request = factory.get("/users/")
    request.user = admin_user

    view = SimpleNamespace(action="list")

    permission = IsAdminOrOwnerProfile()
    assert permission.has_permission(request, view) is True


@pytest.mark.django_db
def test_permission_update_allowed_for_owner(normal_user):
    factory = APIRequestFactory()
    request = factory.put("/users/1/")
    request.user = normal_user

    view = SimpleNamespace(action="update")

    permission = IsAdminOrOwnerProfile()
    assert permission.has_permission(request, view) is True


@pytest.mark.django_db
def test_object_permission_owner(normal_user):
    request = APIRequestFactory().get("/users/1/")
    request.user = normal_user

    view = SimpleNamespace(action="retrieve")

    permission = IsAdminOrOwnerProfile()
    assert permission.has_object_permission(request, view, normal_user) is True


@pytest.mark.django_db
def test_object_permission_not_owner(normal_user, admin_user):
    request = APIRequestFactory().get("/users/1/")
    request.user = normal_user

    view = SimpleNamespace(action="retrieve")

    permission = IsAdminOrOwnerProfile()
    assert permission.has_object_permission(request, view, admin_user) is False
