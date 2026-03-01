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

EXPORT_COLUMN_LABELS = {
    "id": "ID",
    "first_name": "Prenom",
    "last_name": "Nom",
    "email": "Email",
    "phone_number": "Telephone",
    "role": "Role",
    "is_active": "Actif",
    "last_login": "Derniere connexion",
    "created_at": "Cree le",
    "updated_at": "Mis a jour le",
}

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 500
DEFAULT_PAGE = 1


def _user_filter_parameters(
    include_file_format=False, include_page_size=False, include_page=False
):
    params = [
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
    ]

    if include_page_size:
        params.append(
            OpenApiParameter(
                name="page_size",
                description=(
                    "Nombre d'utilisateurs renvoyes par la recherche "
                    f"(defaut: {DEFAULT_PAGE_SIZE}, max: {MAX_PAGE_SIZE})"
                ),
                required=False,
                type=int,
            )
        )

    if include_page:
        params.append(
            OpenApiParameter(
                name="page",
                description=f"Numero de page (defaut: {DEFAULT_PAGE})",
                required=False,
                type=int,
            )
        )

    if include_file_format:
        params.append(
            OpenApiParameter(
                name="file_format",
                description="Format de sortie (csv|pdf). Par defaut: csv",
                required=False,
                type=str,
            )
        )

    return params


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

    @staticmethod
    def _parse_page_size(value):
        if value in (None, ""):
            return DEFAULT_PAGE_SIZE

        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return DEFAULT_PAGE_SIZE

        if parsed <= 0:
            return DEFAULT_PAGE_SIZE

        return min(parsed, MAX_PAGE_SIZE)

    @staticmethod
    def _parse_page(value):
        if value in (None, ""):
            return DEFAULT_PAGE

        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return DEFAULT_PAGE

        if parsed <= 0:
            return DEFAULT_PAGE

        return parsed

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
        parameters=_user_filter_parameters(include_page_size=True, include_page=True),
    )
    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        queryset = self.get_queryset()
        queryset, query = self._apply_filters(queryset)
        total = queryset.count()
        page_size = self._parse_page_size(request.query_params.get("page_size"))
        page = self._parse_page(request.query_params.get("page"))
        start = (page - 1) * page_size
        end = start + page_size
        queryset = queryset[start:end]
        total_pages = max((total + page_size - 1) // page_size, 1)

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "data": serializer.data,
                "total": total,
                "query": query,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
        )

    @extend_schema(
        tags=["Users"],
        summary="Exporter des utilisateurs (CSV ou PDF)",
        parameters=_user_filter_parameters(include_file_format=True),
    )
    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        queryset = self.get_queryset()
        queryset, _ = self._apply_filters(queryset)
        queryset = queryset.order_by("id")

        output_format = request.query_params.get("file_format") or "csv"
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
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = "attachment; filename=users.csv"
        # BOM UTF-8 pour que Excel detecte correctement l'encodage.
        response.write("\ufeff")

        # Delimiteur ';' pour un affichage en colonnes correct dans Excel FR
        writer = csv.writer(response, delimiter=";", lineterminator="\n")
        # Indique explicitement le separateur pour Excel.
        response.write("sep=;\n")
        writer.writerow([EXPORT_COLUMN_LABELS[column] for column in EXPORT_COLUMNS])

        for user in queryset:
            writer.writerow(self._format_export_values(self._user_export_values(user)))

        return response

    @staticmethod
    def _format_export_values(values):
        formatted = []
        for value in values:
            if value is None:
                formatted.append("")
            elif isinstance(value, bool):
                formatted.append("Oui" if value else "Non")
            else:
                formatted.append(str(value))
        return formatted

    def _export_pdf(self, queryset):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import (
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )
        except ImportError:
            return Response(
                {"detail": "Le package reportlab est requis pour l'export PDF."},
                status=500,
            )

        buffer = io.BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            leftMargin=24,
            rightMargin=24,
            topMargin=24,
            bottomMargin=24,
        )
        styles = getSampleStyleSheet()

        title = Paragraph("PrimeBank - Export utilisateurs", styles["Heading2"])
        subtitle = Paragraph(
            f"Total utilisateurs: {queryset.count()}",
            styles["Normal"],
        )

        table_headers = [EXPORT_COLUMN_LABELS[column] for column in EXPORT_COLUMNS]
        table_rows = [table_headers]

        for user in queryset:
            row = self._format_export_values(self._user_export_values(user))
            table_rows.append(row)

        table = Table(table_rows, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#F8FAFC")],
                    ),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        document.build([title, subtitle, Spacer(1, 12), table])
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
