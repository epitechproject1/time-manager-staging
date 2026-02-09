from datetime import timedelta

import pytest
from django.utils import timezone

from plannings.models import Planning


@pytest.fixture
def planning_owned_by_normal_user(db, normal_user):
    return Planning.objects.create(
        title="My Planning",
        start_datetime=timezone.now(),
        end_datetime=timezone.now() + timedelta(hours=2),
        user=normal_user,
        team_id=None,
    )


@pytest.fixture
def planning_owned_by_admin(db, admin_user):
    return Planning.objects.create(
        title="Admin Planning",
        start_datetime=timezone.now(),
        end_datetime=timezone.now() + timedelta(hours=3),
        user=admin_user,
        team_id=None,
    )
