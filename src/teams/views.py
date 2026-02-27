import csv
import io
import logging
from datetime import datetime

from django.core.cache import cache
from django.db.models import (
    Case,
    CharField,
    Count,
    Exists,
    IntegerField,
    OuterRef,
    Q,
    Value,
    When,
)
from django.db.models.functions import Concat, Lower
from django.http import HttpResponse
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from users.constants import UserRole

from .models import Teams
from .permissions import IsAdminOrReadOnlyTeamsDirectory
from .serializers import TeamsLiteSerializer, TeamsSerializer, UserMiniSerializer

logger = logging.getLogger(__name__)
TEAMS_CACHE_PATTERN = "teams:*"

VALID_ORDERINGS = {
    "name",
    "-name",
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
    "members_count",
    "-members_count",
}
ADMIN_ROLES = (getattr(UserRole, "ADMIN", "ADMIN"), "ADMIN", "ADMINISTRATEUR")
MANAGER_ROLES = (getattr(UserRole, "MANAGER", "MANAGER"), "MANAGER")


def _role_str(v) -> str:
    return "" if v is None else str(v).strip().upper()


def is_role(user, *roles) -> bool:
    current = _role_str(getattr(user, "role", None))
    return any(current == _role_str(r) for r in roles if r is not None)


def safe_cache_delete_pattern(pattern: str) -> None:
    try:
        delete_pattern = getattr(cache, "delete_pattern", None)
        if callable(delete_pattern):
            delete_pattern(pattern)
        else:
            logger.warning(
                "Cache backend ne supporte pas delete_pattern(). Pattern ignoré: %s",
                pattern,
            )
    except Exception:
        logger.exception("Erreur lors de la suppression du cache pattern: %s", pattern)


@extend_schema_view(
    list=extend_schema(
        tags=["Teams"],
        summary="Lister les équipes",
        description="Annuaire des équipes (Lite) + filtres + tri",
        parameters=[
            OpenApiParameter(
                name="q", description="Recherche", required=False, type=str
            ),
            OpenApiParameter(
                name="department_id",
                description="Département",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="owner_id", description="Owner", required=False, type=int
            ),
            OpenApiParameter(
                name="my_teams", description="Mes équipes", required=False, type=bool
            ),
            OpenApiParameter(
                name="ordering", description="Tri", required=False, type=str
            ),
        ],
    ),
    retrieve=extend_schema(tags=["Teams"], summary="Détail d'une équipe"),
    create=extend_schema(tags=["Teams"], summary="Créer une équipe"),
    update=extend_schema(tags=["Teams"], summary="Mettre à jour une équipe"),
    partial_update=extend_schema(tags=["Teams"], summary="Mise à jour partielle"),
    destroy=extend_schema(tags=["Teams"], summary="Supprimer une équipe"),
)
class TeamsViewSet(ModelViewSet):
    serializer_class = TeamsSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnlyTeamsDirectory]

    filter_backends = [OrderingFilter]
    ordering_fields = ["name", "created_at", "updated_at", "members_count"]
    ordering = ["-created_at"]

    def _is_scoped_team(self, team: Teams) -> bool:
        """
        Scoped si:
        - admin
        - owner
        - membre
        - director du département de la team
        """
        user = self.request.user
        if user.role == UserRole.ADMIN:
            return True
        if team.owner_id == user.id:
            return True
        if team.members.filter(id=user.id).exists():
            return True
        if (
            team.department_id
            and getattr(team.department, "director_id", None) == user.id
        ):
            return True
        return False

    def get_serializer_class(self):
        if self.action in ("list", "search", "my_teams"):
            return TeamsLiteSerializer

        if self.action == "retrieve":
            team = self.get_object()
            return (
                TeamsSerializer if self._is_scoped_team(team) else TeamsLiteSerializer
            )

        return TeamsSerializer

    def get_queryset(self):
        qs = (
            Teams.objects.all()
            .select_related("owner", "department", "department__director")
            .prefetch_related("members")
            .annotate(members_count=Count("members", distinct=True))
        )

        search_term = (self.request.query_params.get("q") or "").strip()
        if search_term and self.action in ("list", "search", "my_teams"):
            qs = qs.filter(
                Q(name__icontains=search_term)
                | Q(description__icontains=search_term)
                | Q(department__name__icontains=search_term)
                | Q(owner__first_name__icontains=search_term)
                | Q(owner__last_name__icontains=search_term)
                | Q(owner__email__icontains=search_term)
            )

        department_id = self.request.query_params.get("department_id")
        if department_id:
            qs = qs.filter(department_id=department_id)

        owner_id = self.request.query_params.get("owner_id")
        if owner_id:
            qs = qs.filter(owner_id=owner_id)

        my_teams_param = (
            (self.request.query_params.get("my_teams") or "").strip().lower()
        )
        if my_teams_param in ("1", "true", "yes", "y", "on"):
            qs = qs.filter(owner=self.request.user)

        user = self.request.user

        if user.is_authenticated and not is_role(user, *ADMIN_ROLES):
            through = Teams.members.through
            is_member = Exists(
                through.objects.filter(teams_id=OuterRef("pk"), user_id=user.id)
            )

            qs = qs.annotate(
                _is_member=is_member,
                is_pinned=Case(
                    When(owner_id=user.id, then=Value(1)),
                    When(_is_member=True, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
            ).order_by("-is_pinned", "-created_at", "id")
        else:
            qs = qs.order_by("-created_at", "id")

        return qs

    def filter_queryset(self, queryset):

        qs = super().filter_queryset(queryset)

        ordering = (self.request.query_params.get("ordering") or "").strip()
        if not ordering:
            return qs

        if ordering not in VALID_ORDERINGS:
            return qs

        if ordering in ("name", "-name"):
            desc = ordering.startswith("-")
            return qs.annotate(_name_ci=Lower("name")).order_by(
                ("-" if desc else "") + "_name_ci",
                "id",
            )

        return qs.order_by(ordering, "id")

    def list(self, request, *args, **kwargs):
        """
        Réponse uniforme pour le front: {data, total, query}
        même quand la pagination DRF est active.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            total = getattr(getattr(self, "paginator", None), "page", None)
            total = total.paginator.count if total else queryset.count()
            return Response(
                {
                    "data": serializer.data,
                    "total": total,
                    "query": request.query_params.get("q", ""),
                }
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "data": serializer.data,
                "total": queryset.count(),
                "query": request.query_params.get("q", ""),
            }
        )

    def perform_create(self, serializer):
        safe_cache_delete_pattern(TEAMS_CACHE_PATTERN)
        serializer.save()

    def perform_update(self, serializer):
        safe_cache_delete_pattern(TEAMS_CACHE_PATTERN)
        serializer.save()

    def perform_destroy(self, instance):
        safe_cache_delete_pattern(TEAMS_CACHE_PATTERN)
        instance.delete()

    @extend_schema(tags=["Teams"], summary="Lister/Rechercher les membres d'une équipe")
    @action(detail=True, methods=["get"], url_path="members")
    def members(self, request, pk=None):
        team = self.get_object()
        q = (request.query_params.get("q") or "").strip()
        ordering = (request.query_params.get("ordering") or "").strip()

        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except (ValueError, TypeError):
            page = 1

        try:
            page_size = int(request.query_params.get("page_size", 6))
        except (ValueError, TypeError):
            page_size = 6
        page_size = min(max(page_size, 1), 100)

        qs = team.members.all().annotate(
            full_name=Concat(
                "first_name",
                Value(" "),
                "last_name",
                output_field=CharField(),
            ),
            full_name_reversed=Concat(
                "last_name",
                Value(" "),
                "first_name",
                output_field=CharField(),
            ),
        )

        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
                | Q(full_name__icontains=q)
                | Q(full_name_reversed__icontains=q)
            )

        allowed = {
            "first_name",
            "-first_name",
            "last_name",
            "-last_name",
            "email",
            "-email",
        }
        if ordering in allowed:
            qs = qs.order_by(ordering, "id")
        else:
            qs = qs.order_by("first_name", "last_name", "id")

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        serializer = UserMiniSerializer(qs[start:end], many=True)
        return Response(
            {
                "count": total,
                "next": page * page_size < total,
                "previous": page > 1,
                "results": serializer.data,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size if total else 0,
            }
        )

    @action(detail=False, methods=["get"], url_path="my-teams")
    def my_teams(self, request):
        queryset = self.filter_queryset(self.get_queryset().filter(owner=request.user))
        serializer = TeamsLiteSerializer(queryset, many=True)
        return Response({"data": serializer.data, "total": queryset.count()})

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        search_term = (request.query_params.get("q") or "").strip()

        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except ValueError:
            page = 1

        try:
            limit = int(request.query_params.get("limit", 10))
        except ValueError:
            limit = 10
        limit = min(max(limit, 1), 100)

        cache_key = f"teams:search:{search_term}:{page}:{limit}:{request.user.id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return Response(cached_result)

        queryset = self.filter_queryset(self.get_queryset())
        total = queryset.count()

        start = (page - 1) * limit
        end = start + limit
        teams = queryset[start:end]

        serializer = TeamsLiteSerializer(teams, many=True)
        response_data = {
            "data": serializer.data,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if total else 0,
            "query": search_term,
        }

        cache.set(cache_key, response_data, 300)
        return Response(response_data)

    @action(detail=False, methods=["get"], url_path="export/csv")
    def export_csv(self, request):
        user = request.user

        if not (is_role(user, *ADMIN_ROLES) or is_role(user, *MANAGER_ROLES)):
            raise PermissionDenied(
                "Accès refusé. Seul l'administrateur ou le manager peut exporter."
            )

        qs = self.filter_queryset(self.get_queryset())

        # ✅ manager exporte uniquement ses équipes (responsable = owner)
        if is_role(user, *MANAGER_ROLES) and not is_role(user, *ADMIN_ROLES):
            qs = qs.filter(owner=user)
            if not qs.exists():
                raise PermissionDenied(
                    "Vous n’êtes responsable d’aucune équipe. Export impossible."
                )

        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="teams_export.csv"'
        response.write("\ufeff")

        writer = csv.writer(response)
        writer.writerow(
            [
                "id",
                "name",
                "description",
                "department_id",
                "department_name",
                "owner_id",
                "owner_email",
                "members_count",
            ]
        )

        for t in qs:
            writer.writerow(
                [
                    t.id,
                    t.name,
                    t.description or "",
                    t.department_id or "",
                    getattr(getattr(t, "department", None), "name", "") or "",
                    t.owner_id or "",
                    getattr(getattr(t, "owner", None), "email", "") or "",
                    getattr(t, "members_count", 0) or 0,
                ]
            )

        return response

    @action(
        detail=False,
        methods=["post"],
        url_path="import/csv",
        parser_classes=[MultiPartParser, FormParser],
    )
    def import_csv(self, request):
        if request.user.role != UserRole.ADMIN:
            raise PermissionDenied("Accès refusé.")

        file = request.FILES.get("file")
        if not file:
            raise ValidationError({"file": "Fichier CSV requis (field name = file)."})

        try:
            content = file.read().decode("utf-8-sig")
        except Exception:
            raise ValidationError({"file": "Impossible de lire le fichier en UTF-8."})

        reader = csv.DictReader(io.StringIO(content))
        required_cols = {"name"}
        if not reader.fieldnames or not required_cols.issubset(set(reader.fieldnames)):
            raise ValidationError(
                {"file": f"Colonnes requises: {sorted(required_cols)}"}
            )

        created = 0
        updated = 0
        errors = []

        for i, row in enumerate(reader, start=2):
            try:
                name = (row.get("name") or "").strip()
                if not name:
                    raise ValueError("name vide")

                description = (row.get("description") or "").strip() or None
                department_id = row.get("department_id")
                owner_id = row.get("owner_id")

                department_id = (
                    int(department_id) if str(department_id).strip() else None
                )
                owner_id = int(owner_id) if str(owner_id).strip() else None

                obj, is_created = Teams.objects.update_or_create(
                    name=name,
                    defaults={
                        "description": description,
                        "department_id": department_id,
                        "owner_id": owner_id,
                    },
                )
                created += 1 if is_created else 0
                updated += 0 if is_created else 1

            except Exception as e:
                errors.append({"line": i, "error": str(e), "row": row})

        safe_cache_delete_pattern(TEAMS_CACHE_PATTERN)

        return Response(
            {
                "created": created,
                "updated": updated,
                "errors": errors,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="export/pdf")
    def export_pdf(self, request):
        user = request.user

        if not (is_role(user, *ADMIN_ROLES) or is_role(user, *MANAGER_ROLES)):
            raise PermissionDenied(
                "Accès refusé. Seul l'administrateur ou le manager peut exporter."
            )

        qs = self.filter_queryset(self.get_queryset()).prefetch_related("members")

        # ✅ manager exporte uniquement ses équipes (responsable = owner)
        if is_role(user, *MANAGER_ROLES) and not is_role(user, *ADMIN_ROLES):
            qs = qs.filter(owner=user)
            if not qs.exists():
                raise PermissionDenied(
                    "Vous n’êtes responsable d’aucune équipe. Export impossible."
                )

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="teams_export.pdf"'

        from reportlab.lib.pagesizes import A4, landscape

        c = canvas.Canvas(response, pagesize=landscape(A4))
        width, height = landscape(A4)

        # ── Couleurs ─────────────────────────────────────────────────────────
        BLUE = (0.12, 0.39, 0.78)
        GRAY_DARK = (0.20, 0.20, 0.20)
        GRAY_MID = (0.50, 0.50, 0.50)
        GRAY_LIGHT = (0.95, 0.95, 0.95)
        WHITE = (1.0, 1.0, 1.0)

        MARGIN_X = 1.5 * cm
        MARGIN_Y = 1.5 * cm
        TABLE_W = width - 2 * MARGIN_X

        # ── Colonnes ─────────────────────────────────────────────────────────
        COLS = [
            ("ID", 0.05),
            ("Équipe", 0.14),
            ("Description", 0.18),
            ("Département", 0.12),
            ("Responsable", 0.13),
            ("Email", 0.19),
            ("Membres", 0.06),
            ("Liste membres", 0.13),
        ]
        col_widths = [TABLE_W * r for _, r in COLS]
        col_labels = [label for label, _ in COLS]
        ROW_H_BASE = 0.65 * cm
        HEADER_H = 0.80 * cm

        # ── Helpers couleur ──────────────────────────────────────────────────
        def rgb(c_obj, color):
            c_obj.setFillColorRGB(*color)

        def stroke(c_obj, color):
            c_obj.setStrokeColorRGB(*color)

        def truncate(text, max_chars):
            text = str(text)
            return text if len(text) <= max_chars else text[: max_chars - 1] + "…"

        def max_chars_for(col_w, font_size=8):
            return max(int(col_w / (font_size * 0.50)), 6)

        # ── En-tête document ─────────────────────────────────────────────────
        def draw_doc_header(c, y):
            c.setFillColorRGB(*BLUE)
            c.rect(MARGIN_X, y - 1.4 * cm, TABLE_W, 1.4 * cm, fill=1, stroke=0)
            c.setFillColorRGB(*WHITE)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(MARGIN_X + 0.4 * cm, y - 0.95 * cm, "Gestion des Équipes")
            c.setFont("Helvetica", 9)
            date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
            c.drawRightString(
                width - MARGIN_X - 0.2 * cm, y - 0.95 * cm, f"Exporté le {date_str}"
            )

            c.setFillColorRGB(*GRAY_MID)
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(MARGIN_X, y - 1.75 * cm, f"{qs.count()} équipe(s) exportée(s)")

            return y - 2.2 * cm

        # ── En-tête tableau ──────────────────────────────────────────────────
        def draw_table_header(c, y):
            c.setFillColorRGB(*BLUE)
            c.rect(MARGIN_X, y - HEADER_H, TABLE_W, HEADER_H, fill=1, stroke=0)
            c.setFillColorRGB(*WHITE)
            c.setFont("Helvetica-Bold", 8)
            x = MARGIN_X
            for label, cw in zip(col_labels, col_widths):
                c.drawString(x + 0.15 * cm, y - HEADER_H + 0.22 * cm, label)
                x += cw
            return y - HEADER_H

        # ── Ligne de données ─────────────────────────────────────────────────
        def draw_row(c, y, row_data, row_index):
            bg = GRAY_LIGHT if row_index % 2 == 0 else WHITE
            c.setFillColorRGB(*bg)
            c.rect(MARGIN_X, y - ROW_H_BASE, TABLE_W, ROW_H_BASE, fill=1, stroke=0)
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.setLineWidth(0.3)
            c.line(MARGIN_X, y - ROW_H_BASE, MARGIN_X + TABLE_W, y - ROW_H_BASE)

            c.setFillColorRGB(*GRAY_DARK)
            c.setFont("Helvetica", 7.5)
            x = MARGIN_X
            for value, cw in zip(row_data, col_widths):
                text = truncate(value, max_chars_for(cw, 7.5))
                c.drawString(x + 0.15 * cm, y - ROW_H_BASE + 0.18 * cm, text)
                x += cw

            return y - ROW_H_BASE

        # ── Bloc membres (multi-lignes) ───────────────────────────────────────
        def draw_members_block(c, y, members, row_index):
            """
            Affiche chaque membre sur sa propre sous-ligne :
            Prénom Nom — email
            """
            if not members:
                return draw_row(c, y, ["—"] * len(col_labels), row_index)

            lines = [f"{m.first_name} {m.last_name}  •  {m.email}" for m in members]

            row_h = max(ROW_H_BASE, len(lines) * 0.50 * cm + 0.20 * cm)

            bg = GRAY_LIGHT if row_index % 2 == 0 else WHITE
            c.setFillColorRGB(*bg)
            c.rect(MARGIN_X, y - row_h, TABLE_W, row_h, fill=1, stroke=0)

            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.setLineWidth(0.3)
            c.line(MARGIN_X, y - row_h, MARGIN_X + TABLE_W, y - row_h)

            return y - row_h, row_h

        # ── Pied de page ─────────────────────────────────────────────────────
        def draw_footer(c, page_num):
            c.setStrokeColorRGB(*GRAY_MID)
            c.setLineWidth(0.5)
            c.line(MARGIN_X, MARGIN_Y, width - MARGIN_X, MARGIN_Y)
            c.setFillColorRGB(*GRAY_MID)
            c.setFont("Helvetica", 7)
            c.drawString(
                MARGIN_X, MARGIN_Y - 0.35 * cm, "Time Manager — Export confidentiel"
            )
            c.drawRightString(
                width - MARGIN_X, MARGIN_Y - 0.35 * cm, f"Page {page_num}"
            )

        # ── Nouvelle page ─────────────────────────────────────────────────────
        def new_page(c, page_num):
            draw_footer(c, page_num)
            c.showPage()
            page_num += 1
            y = height - MARGIN_Y
            y = draw_table_header(c, y)
            return y, page_num

        # Rendu
        page_num = 1
        y = height - MARGIN_Y
        y = draw_doc_header(c, y)
        y -= 0.3 * cm
        y = draw_table_header(c, y)

        for row_index, t in enumerate(qs):
            dept = getattr(getattr(t, "department", None), "name", "") or "-"
            owner = getattr(t, "owner", None)
            owner_name = (
                f"{owner.first_name} {owner.last_name}".strip() if owner else "-"
            )
            owner_email = owner.email if owner else "-"
            members = list(t.members.all().order_by("first_name", "last_name"))
            members_count = str(getattr(t, "members_count", len(members)))
            desc = (t.description or "-").replace("\n", " ")

            # Hauteur nécessaire pour cette ligne (1 sous-ligne par membre)
            n_member_lines = max(len(members), 1)
            needed_h = max(ROW_H_BASE, n_member_lines * 0.50 * cm + 0.20 * cm)

            if y - needed_h < MARGIN_Y + 1.0 * cm:
                y, page_num = new_page(c, page_num)

            # ── Fond de ligne ─────────────────────────────────────────────
            bg = GRAY_LIGHT if row_index % 2 == 0 else WHITE
            c.setFillColorRGB(*bg)
            c.rect(MARGIN_X, y - needed_h, TABLE_W, needed_h, fill=1, stroke=0)
            c.setStrokeColorRGB(0.85, 0.85, 0.85)
            c.setLineWidth(0.3)
            c.line(MARGIN_X, y - needed_h, MARGIN_X + TABLE_W, y - needed_h)

            # ── Données fixes (toutes colonnes sauf liste membres) ────────
            fixed_data = [
                str(t.id),
                t.name,
                desc,
                dept,
                owner_name,
                owner_email,
                members_count,
            ]

            c.setFont("Helvetica", 7.5)
            c.setFillColorRGB(*GRAY_DARK)

            x = MARGIN_X
            for value, cw in zip(fixed_data, col_widths[:-1]):
                text = truncate(value, max_chars_for(cw, 7.5))
                c.drawString(x + 0.15 * cm, y - ROW_H_BASE + 0.18 * cm, text)
                x += cw

            # ── Colonne "Liste membres" : une sous-ligne par membre ───────
            member_x = x
            member_col_w = col_widths[-1]
            sub_y = y - 0.18 * cm

            if members:
                c.setFont("Helvetica", 7)
                for m in members:
                    member_line = f"{m.first_name} {m.last_name}"
                    email_line = m.email
                    c.setFillColorRGB(*GRAY_DARK)
                    c.drawString(
                        member_x + 0.15 * cm,
                        sub_y - 0.28 * cm,
                        truncate(member_line, max_chars_for(member_col_w, 7)),
                    )
                    c.setFont("Helvetica-Oblique", 6.5)
                    c.setFillColorRGB(*GRAY_MID)
                    c.drawString(
                        member_x + 0.15 * cm,
                        sub_y - 0.48 * cm,
                        truncate(email_line, max_chars_for(member_col_w, 6.5)),
                    )
                    c.setFont("Helvetica", 7)
                    sub_y -= 0.50 * cm
            else:
                c.setFillColorRGB(*GRAY_MID)
                c.setFont("Helvetica-Oblique", 7.5)
                c.drawString(
                    member_x + 0.15 * cm, y - ROW_H_BASE + 0.18 * cm, "Aucun membre"
                )

            y -= needed_h

        draw_footer(c, page_num)
        c.showPage()
        c.save()
        return response

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        try:
            now = datetime.now()
            total_teams = Teams.objects.count()

            departments_count = (
                Teams.objects.filter(department__isnull=False)
                .values("department")
                .distinct()
                .count()
            )

            this_month_count = Teams.objects.filter(
                created_at__year=now.year, created_at__month=now.month
            ).count()

            user_teams_count = Teams.objects.filter(owner=request.user).count()

            teams_by_department = (
                Teams.objects.values("department__id", "department__name")
                .annotate(count=Count("id"))
                .order_by("-count")[:5]
            )

            return Response(
                {
                    "total_teams": total_teams,
                    "departments_count": departments_count,
                    "this_month_count": this_month_count,
                    "user_teams_count": user_teams_count,
                    "teams_by_department": list(teams_by_department),
                    "timestamp": now.isoformat(),
                }
            )
        except Exception as e:
            logger.error("Erreur stats: %s", str(e), exc_info=True)
            return Response(
                {"error": "Erreur lors du calcul des statistiques"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
