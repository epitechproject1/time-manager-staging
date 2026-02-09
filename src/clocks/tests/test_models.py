import pytest


@pytest.mark.django_db
def test_create_clock(clock):
    assert clock.work_date is not None
    assert clock.clock_in is not None
    assert clock.created_at is not None


@pytest.mark.django_db
def test_clock_default_status(clock):
    assert clock.status == "pending"


@pytest.mark.django_db
def test_clock_str(clock):
    assert str(clock) == f"{clock.user.email} - {clock.work_date}"
