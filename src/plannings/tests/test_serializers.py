from datetime import timedelta

import pytest
from django.utils import timezone

from plannings.serializers import PlanningSerializer


@pytest.mark.django_db
def test_serializer_rejects_end_before_start(normal_user, api_client):
    now = timezone.now()
    serializer = PlanningSerializer(
        data={
            "title": "Bad",
            "start_datetime": now,
            "end_datetime": now - timedelta(hours=1),
            "user": normal_user.id,
            "planning_type": "SHIFT",
            "work_mode": "REMOTE",
        }
    )
    assert not serializer.is_valid()
    assert "end_datetime" in serializer.errors
