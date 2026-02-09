import pytest

from clocks.serializers import ClockSerializer


@pytest.mark.django_db
def test_clock_serializer_read_only_fields(clock):
    serializer = ClockSerializer(clock)
    data = serializer.data

    assert data["user"] == clock.user.id
    assert data["work_date"] == "2026-02-09"
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.django_db
def test_clock_create_serializer_success(user):
    serializer = ClockSerializer(
        data={
            "user": user.id,
            "work_date": "2026-02-10",
            "clock_in": "09:00:00",
        }
    )

    assert serializer.is_valid(), serializer.errors
    clock = serializer.save()

    assert clock.user == user
    assert clock.status == "pending"
