from rest_framework import serializers


class AttendanceKPISerializer(serializers.Serializer):
    planned_shifts = serializers.IntegerField()
    worked_shifts = serializers.IntegerField()
    attendance_rate = serializers.FloatField()

    late_count = serializers.IntegerField()

    worked_seconds = serializers.IntegerField()

    incomplete_shifts = serializers.IntegerField()
    missed_shifts = serializers.IntegerField()

    today_status = serializers.CharField(allow_null=True)
