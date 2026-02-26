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

EXPORT_COLUMNS = (
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
)


def _user_filter_parameters(include_file_format=False):
    params = [
        OpenApiParameter(
            "q", description="Recherche globale", required=False, type=str
        ),
        OpenApiParameter(
            "role", description="Filtrer par role", required=False, type=str
        ),
        OpenApiParameter(
            "email", description="Filtrer par email", required=False, type=str
        ),
        OpenApiParameter(
            "is_active", description="Filtrer par actif", required=False, type=bool
        ),
        OpenApiParameter(
            "created_from", description="Date min", required=False, type=str
        ),
        OpenApiParameter(
            "created_to", description="Date max", required=False, type=str
        ),
        OpenApiParameter("ordering", description="Tri", required=False, type=str),
    ]

    if include_file_format:
        params.append(
            OpenApiParameter(
                "file_format",
                description="csv ou pdf",
                required=False,
                type=str,
            )
        )

    return params


@extend_schema_view(
    list=extend_schema(tags=["Users"], summary="Lister les utilisateurs"),
    retrieve=extend_schema(tags=["Users"], summary="Detail utilisateur"),
    create=extend_schema(tags=["Users"], summary="Creer utilisateur"),
    update=extend_schema(tags=["Users"], summary="Mettre a jour utilisateur"),
    partial_update=extend_schema(tags=["Users"], summary="Patch utilisateur"),
    destroy=extend_schema(tags=["Users"], summary="Supprimer utilisateur"),
)
class UserViewSet(ModelViewSet):
    permission_classes = [IsAdminOrOwnerProfile]

    # ----------------------------------------------------------------
    # Queryset & Serializer
    # ----------------------------------------------------------------

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

    # ----------------------------------------------------------------
    # Utils
    # ----------------------------------------------------------------

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

    # ----------------------------------------------------------------
    # Hooks
    # ----------------------------------------------------------------

    def perform_create(self, serializer):
        user = serializer.save()
        raw_password = self.request.data.get("password")

        if raw_password:
            run_async(send_welcome_email, user, raw_password)

    # ----------------------------------------------------------------
    # Custom actions
    # ----------------------------------------------------------------

    @extend_schema(summary="Profil utilisateur connecté")
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        tags=["Users"],
        summary="Rechercher des utilisateurs",
        parameters=_user_filter_parameters(),
    )
    @action(detail=False, methods=["get"])
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
        summary="Exporter utilisateurs",
        parameters=_user_filter_parameters(include_file_format=True),
    )
    @action(detail=False, methods=["get"])
    def export(self, request):
        queryset = self.get_queryset()
        queryset, _ = self._apply_filters(queryset)

        output_format = (request.query_params.get("file_format") or "csv").lower()

        if output_format == "pdf":
            return self._export_pdf(queryset)
        if output_format != "csv":
            return Response({"detail": "Format invalide (csv|pdf)"}, status=400)

        return self._export_csv(queryset)

    # ----------------------------------------------------------------
    # Export helpers
    # ----------------------------------------------------------------

    def _export_csv(self, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=users.csv"

        writer = csv.writer(response)
        writer.writerow(EXPORT_COLUMNS)

        for user in queryset:
            writer.writerow(self._user_export_values(user))

        return response

    def _export_pdf(self, queryset):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except ImportError:
            return Response({"detail": "reportlab requis"}, status=500)

        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 40

        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(40, y, "Export utilisateurs")
        y -= 24

        pdf.setFont("Helvetica", 9)
        pdf.drawString(40, y, f"Total: {queryset.count()}")
        y -= 22

        for user in queryset:
            for line in self._user_export_values(user):
                pdf.drawString(40, y, str(line))
                y -= 14
            y -= 10

        pdf.save()
        pdf_data = buffer.getvalue()
        buffer.close()

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = "attachment; filename=users.pdf"
        response.write(pdf_data)
        return response

    @staticmethod
    def _user_export_values(user):
        return [
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
