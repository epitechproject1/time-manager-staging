import pytest
from rest_framework.test import APIClient

from clocks.models import Clock
from users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="user@test.com",
        password="password",
        first_name="Normal",
        last_name="User",
    )


@pytest.fixture
def clock(db, user):
    return Clock.objects.create(
        user=user,
        work_date="2026-02-09",
        clock_in="08:00:00",
        clock_out="17:00:00",
    )
