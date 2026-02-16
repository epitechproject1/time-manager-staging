import csv
import io

from django.db.models import Q
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from notifications.services import send_welcome_email
from notifications.utils import run_async

from .constants import UserRole
from .models import User
from .permissions import IsAdminOrOwnerProfile
from .serializers import UserCreateSerializer, UserSerializer, UserUpdateSerializer


@extend_schema_view(
    list=extend_schema(tags=["Users"], summary="Lister les utilisateurs"),
    retrieve=extend_schema(tags=["Users"], summary="Detail d'un utilisateur"),
    create=extend_schema(tags=["Users"], summary="Creer un utilisateur"),
    update=extend_schema(tags=["Users"], summary="Mettre a jour un utilisateur"),
    partial_update=extend_schema(
        tags=["Users"], summary="Mettre a jour partiellement un utilisateur"
    ),
    destroy=extend_schema(tags=["Users"], summary="Supprimer un utilisateur"),
)
class UserViewSet(ModelViewSet):
    permission_classes = [IsAdminOrOwnerProfile]

    @staticmethod
    def _parse_bool(value):
        if value is None:
            return None

        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False

        return None

    def _apply_filters(self, queryset):
        query = (self.request.query_params.get("q") or "").strip()
        role = (self.request.query_params.get("role") or "").strip()
        email = (self.request.query_params.get("email") or "").strip()
        is_active_raw = self.request.query_params.get("is_active")
        created_from = parse_date(self.request.query_params.get("created_from", ""))
        created_to = parse_date(self.request.query_params.get("created_to", ""))
        ordering = (self.request.query_params.get("ordering") or "").strip()

        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
                | Q(phone_number__icontains=query)
                | Q(role__icontains=query)
            )

        if role:
            queryset = queryset.filter(role=role)

        if email:
            queryset = queryset.filter(email__icontains=email)

        is_active = self._parse_bool(is_active_raw)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)

        if created_from:
            queryset = queryset.filter(created_at__date__gte=created_from)

        if created_to:
            queryset = queryset.filter(created_at__date__lte=created_to)

        allowed_ordering = {
            "id",
            "-id",
            "first_name",
            "-first_name",
            "last_name",
            "-last_name",
            "email",
            "-email",
            "role",
            "-role",
            "is_active",
            "-is_active",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        }
        if ordering and ordering in allowed_ordering:
            queryset = queryset.order_by(ordering)

        return queryset, query

    def get_queryset(self):
        user = self.request.user

        if user.role == UserRole.ADMIN:
            return User.objects.all().order_by("-created_at")

        return User.objects.filter(id=user.id)

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer

        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer

        return UserSerializer

    def perform_create(self, serializer):
        """
        Creation utilisateur + envoi email async
        """
        user = serializer.save()

        raw_password = self.request.data.get("password")

        if raw_password:
            run_async(send_welcome_email, user, raw_password)

    @extend_schema(summary="Recuperer le profil de l'utilisateur connecte")
    @action(
        detail=False,
        methods=["get"],
        url_path="me",
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        tags=["Users"],
        summary="Rechercher des utilisateurs",
        parameters=[
            OpenApiParameter(
                name="q",
                description="Recherche (nom, prenom, email, telephone, role)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="role",
                description="Filtrer par role (ADMIN, MANAGER, USER)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="email",
                description="Filtrer par email (contient)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="is_active",
                description="Filtrer par statut actif (true/false)",
                required=False,
                type=bool,
            ),
            OpenApiParameter(
                name="created_from",
                description="Date de creation min (YYYY-MM-DD)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="created_to",
                description="Date de creation max (YYYY-MM-DD)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="ordering",
                description="Tri (ex: -created_at, email, role)",
                required=False,
                type=str,
            ),
        ],
    )
    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        queryset = self.get_queryset()
        queryset, query = self._apply_filters(queryset)

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "data": serializer.data,
                "total": queryset.count(),
                "query": query,
            }
        )

    @extend_schema(
        tags=["Users"],
        summary="Exporter des utilisateurs (CSV ou PDF)",
        parameters=[
            OpenApiParameter(
                name="q",
                description="Filtrer l'export par recherche",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="role",
                description="Filtrer par role (ADMIN, MANAGER, USER)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="email",
                description="Filtrer par email (contient)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="is_active",
                description="Filtrer par statut actif (true/false)",
                required=False,
                type=bool,
            ),
            OpenApiParameter(
                name="created_from",
                description="Date de creation min (YYYY-MM-DD)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="created_to",
                description="Date de creation max (YYYY-MM-DD)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="ordering",
                description="Tri (ex: -created_at, email, role)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="format",
                description="Format de sortie (csv|pdf). Par defaut: csv",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="file_format",
                description="Alias de format (csv|pdf), prioritaire sur format",
                required=False,
                type=str,
            ),
        ],
    )
    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        queryset = self.get_queryset()
        queryset, _ = self._apply_filters(queryset)

        output_format = (
            request.query_params.get("file_format")
            or request.query_params.get("format")
            or "csv"
        )
        output_format = str(output_format).strip().lower()

        if output_format == "pdf":
            return self._export_pdf(queryset)
        if output_format != "csv":
            return Response(
                {"detail": "Format invalide. Utilisez csv ou pdf."},
                status=400,
            )

        return self._export_csv(queryset)

    def _export_csv(self, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=users.csv"

        writer = csv.writer(response)
        writer.writerow(
            [
                "id",
                "first_name",
                "last_name",
                "email",
                "phone_number",
                "role",
                "is_active",
                "last_login",
                "created_at",
                "updated_at",
            ]
        )

        for user in queryset:
            writer.writerow(
                [
                    user.id,
                    user.first_name,
                    user.last_name,
                    user.email,
                    user.phone_number,
                    user.role,
                    user.is_active,
                    user.last_login,
                    user.created_at,
                    user.updated_at,
                ]
            )

        return response

    def _export_pdf(self, queryset):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except ImportError:
            return Response(
                {"detail": "Le package reportlab est requis pour l'export PDF."},
                status=500,
            )

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 40

        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(40, y, "PrimeBank - Export utilisateurs")
        y -= 24
        pdf.setFont("Helvetica", 9)
        pdf.drawString(40, y, f"Total utilisateurs: {queryset.count()}")
        y -= 22

        for user in queryset:
            lines = [
                f"id: {user.id}",
                f"first_name: {user.first_name}",
                f"last_name: {user.last_name}",
                f"email: {user.email}",
                f"phone_number: {user.phone_number or ''}",
                f"role: {user.role}",
                f"is_active: {user.is_active}",
                f"last_login: {user.last_login or ''}",
                f"created_at: {user.created_at}",
                f"updated_at: {user.updated_at}",
            ]

            needed_height = 14 * (len(lines) + 1)
            if y - needed_height < 40:
                pdf.showPage()
                y = height - 40
                pdf.setFont("Helvetica", 9)

            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(40, y, f"Utilisateur #{user.id}")
            y -= 14

            pdf.setFont("Helvetica", 9)
            for line in lines:
                pdf.drawString(52, y, line)
                y -= 14

            y -= 8

        pdf.save()
        pdf_data = buffer.getvalue()
        buffer.close()

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = "attachment; filename=users.pdf"
        response.write(pdf_data)
        return response
