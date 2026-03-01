from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import AttendanceKPISerializer
from .services import get_attendance_kpis


class KPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_from_param = request.query_params.get("date_from")
        date_to_param = request.query_params.get("date_to")

        date_from = parse_date(date_from_param) if date_from_param else None
        date_to = parse_date(date_to_param) if date_to_param else None

        # Résolution des objets depuis les IDs
        user_id = request.query_params.get("user")
        team_id = request.query_params.get("team")
        department_id = request.query_params.get("department")

        user = None
        team = None
        department = None

        if user_id:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response(
                    {"detail": "Utilisateur introuvable."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        if team_id:
            from teams.models import Teams

            try:
                team = Teams.objects.get(pk=team_id)
            except Teams.DoesNotExist:
                return Response(
                    {"detail": "Équipe introuvable."}, status=status.HTTP_404_NOT_FOUND
                )

        if department_id:
            from departments.models import Department

            try:
                department = Department.objects.get(pk=department_id)
            except Department.DoesNotExist:
                return Response(
                    {"detail": "Département introuvable."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        data = get_attendance_kpis(
            date_from=date_from,
            date_to=date_to,
            user=user,
            team=team,
            department=department,
        )

        serializer = AttendanceKPISerializer(data)
        return Response(serializer.data)
