def test_clock_serializer_invalid_status(user):
    from clocks.serializers import ClockSerializer

    serializer = ClockSerializer(
        data={
            "user": user.id,
            "work_date": "2026-02-09",
            "clock_in": "08:00:00",
            "clock_out": "17:00:00",
            "status": "invalid_status",
        }
    )

    assert serializer.is_valid() is False
    assert "status" in serializer.errors
