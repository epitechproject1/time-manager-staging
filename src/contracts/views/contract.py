import io
from datetime import date

from django.db.models.deletion import ProtectedError
from django.db.models import Q
from django.http import HttpResponse
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from contracts.models import Contract
from contracts.serializers.contract import ContractSerializer
from users.constants import UserRole

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 500
DEFAULT_PAGE = 1


def _contract_search_parameters():
    return [
        OpenApiParameter(
            name="q",
            description="Recherche (nom, prenom, email, type de contrat)",
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name="status",
            description="Filtrer par statut (active|expiring_soon|expired)",
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name="user",
            description="Filtrer par utilisateur (id)",
            required=False,
            type=int,
        ),
        OpenApiParameter(
            name="contract_type",
            description="Filtrer par type de contrat (id)",
            required=False,
            type=int,
        ),
        OpenApiParameter(
            name="page",
            description=f"Numero de page (defaut: {DEFAULT_PAGE})",
            required=False,
            type=int,
        ),
        OpenApiParameter(
            name="page_size",
            description=(
                "Nombre de contrats par page "
                f"(defaut: {DEFAULT_PAGE_SIZE}, max: {MAX_PAGE_SIZE})"
            ),
            required=False,
            type=int,
        ),
        OpenApiParameter(
            name="ordering",
            description="Tri (ex: -start_date, start_date, created_at, -created_at)",
            required=False,
            type=str,
        ),
    ]


def _compute_status(end_date):
    if not end_date:
        return "active"

    today = date.today()
    if end_date < today:
        return "expired"

    if (end_date - today).days <= 30:
        return "expiring_soon"

    return "active"


@extend_schema_view(
    list=extend_schema(
        tags=["Contracts"],
        summary="Lister les contrats",
        description="Liste de tous les contrats.",
    ),
    retrieve=extend_schema(
        tags=["Contracts"],
        summary="Detail d'un contrat",
    ),
    create=extend_schema(
        tags=["Contracts"],
        summary="Creer un contrat",
    ),
    update=extend_schema(
        tags=["Contracts"],
        summary="Mettre a jour un contrat",
    ),
    partial_update=extend_schema(
        tags=["Contracts"],
        summary="Mettre a jour partiellement un contrat",
    ),
    destroy=extend_schema(
        tags=["Contracts"],
        summary="Supprimer un contrat",
    ),
)
class ContractViewSet(ModelViewSet):
    queryset = Contract.objects.select_related("contract_type", "user").all()
    serializer_class = ContractSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Contract.objects.select_related("contract_type", "user").all()

        if getattr(user, "role", None) == UserRole.ADMIN:
            return queryset

        return queryset.filter(user=user)

    def _ensure_admin(self, request):
        if getattr(request.user, "role", None) != UserRole.ADMIN:
            return Response(
                {"detail": "Action reservee aux administrateurs."},
                status=403,
            )
        return None

    def create(self, request, *args, **kwargs):
        denied = self._ensure_admin(request)
        if denied:
            return denied
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        denied = self._ensure_admin(request)
        if denied:
            return denied
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        denied = self._ensure_admin(request)
        if denied:
            return denied
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        denied = self._ensure_admin(request)
        if denied:
            return denied

        instance = self.get_object()
        try:
            self.perform_destroy(instance)
        except ProtectedError:
            return Response(
                {
                    "detail": (
                        "Suppression impossible: ce contrat est utilise par d'autres donnees."
                    )
                },
                status=400,
            )

        return Response(status=204)

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
        status = (self.request.query_params.get("status") or "").strip()
        ordering = (self.request.query_params.get("ordering") or "").strip()
        user_id = self.request.query_params.get("user")
        contract_type_id = self.request.query_params.get("contract_type")

        if query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
                | Q(user__email__icontains=query)
                | Q(contract_type__name__icontains=query)
                | Q(contract_type__code__icontains=query)
            )

        if user_id:
            queryset = queryset.filter(user_id=user_id)

        if contract_type_id:
            queryset = queryset.filter(contract_type_id=contract_type_id)

        today = date.today()
        if status == "active":
            queryset = queryset.filter(Q(end_date__isnull=True) | Q(end_date__gt=today))
        elif status == "expiring_soon":
            from datetime import timedelta

            limit = today + timedelta(days=30)
            queryset = queryset.filter(end_date__gte=today, end_date__lte=limit)
        elif status == "expired":
            queryset = queryset.filter(end_date__lt=today)

        allowed_ordering = {
            "id",
            "-id",
            "start_date",
            "-start_date",
            "end_date",
            "-end_date",
            "created_at",
            "-created_at",
            "weekly_hours_target",
            "-weekly_hours_target",
        }
        if ordering in allowed_ordering:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by("-start_date")

        return queryset, query

    def _compute_stats(self, queryset):
        active = 0
        expiring_soon = 0
        expired = 0

        for contract in queryset:
            status = _compute_status(contract.end_date)
            if status == "active":
                active += 1
            elif status == "expiring_soon":
                expiring_soon += 1
            else:
                expired += 1

        return {
            "total": queryset.count(),
            "active": active,
            "expiring_soon": expiring_soon,
            "expired": expired,
        }

    @extend_schema(
        tags=["Contracts"],
        summary="Rechercher des contrats",
        parameters=_contract_search_parameters(),
    )
    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        queryset = self.get_queryset()
        queryset, query = self._apply_filters(queryset)
        stats = self._compute_stats(queryset)

        page_size = self._parse_page_size(request.query_params.get("page_size"))
        page = self._parse_page(request.query_params.get("page"))
        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        paged_queryset = queryset[start:end]
        total_pages = max((total + page_size - 1) // page_size, 1)

        serializer = self.get_serializer(paged_queryset, many=True)
        return Response(
            {
                "data": serializer.data,
                "total": total,
                "query": query,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "stats": stats,
            }
        )

    @extend_schema(
        tags=["Contracts"],
        summary="Exporter un contrat utilisateur en PDF",
    )
    @action(detail=True, methods=["get"], url_path="export")
    def export(self, request, pk=None):
        contract = self.get_object()
        return self._export_contract_pdf(contract)

    @staticmethod
    def _export_contract_pdf(contract):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import cm
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
        except ImportError:
            return Response(
                {"detail": "Le package reportlab est requis pour l'export PDF."},
                status=500,
            )

        buffer = io.BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=1.8 * cm,
            bottomMargin=1.8 * cm,
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "ContractTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#111827"),
            spaceAfter=14,
        )
        section_style = ParagraphStyle(
            "ContractSection",
            parent=styles["Heading4"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#1F2937"),
            spaceBefore=10,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "ContractBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#111827"),
            spaceAfter=4,
        )

        user_name = f"{contract.user.first_name} {contract.user.last_name}".strip() or contract.user.email
        contract_type_name = contract.contract_type.name or "Contrat"
        contract_label = f"CONTRAT DE TRAVAIL - {contract_type_name}".upper()
        start_date = contract.start_date.strftime("%d/%m/%Y")
        end_date = contract.end_date.strftime("%d/%m/%Y") if contract.end_date else "Durée indéterminée"
        weekly_hours = f"{contract.weekly_hours_target} heures"
        city = "Non renseignée"
        today_str = date.today().strftime("%d/%m/%Y")

        story = [
            Paragraph(f"📄 {contract_label}", title_style),
            Paragraph("Entre les soussignés :", body_style),
            Paragraph(
                (
                    "PrimeBank S.A.,<br/>"
                    "Société Anonyme au capital de XXX €,<br/>"
                    "Siège social : [Adresse complète],<br/>"
                    "Immatriculée au RCS de [Ville] sous le numéro [XXX],<br/>"
                    "Représentée par [Nom, fonction],<br/>"
                    "Ci-après dénommée “l’Employeur”,"
                ),
                body_style,
            ),
            Spacer(1, 6),
            Paragraph("Et :", body_style),
            Paragraph(
                (
                    f"M./Mme {user_name},<br/>"
                    "Né(e) le [Date] à [Lieu],<br/>"
                    "Demeurant [Adresse complète],<br/>"
                    "Numéro de Sécurité Sociale : [XXX],<br/>"
                    "Ci-après dénommé(e) “l’Employé(e)”,"
                ),
                body_style,
            ),
            Spacer(1, 8),
            Paragraph("Il a été convenu ce qui suit :", body_style),
            Paragraph("Article 1 – Objet du contrat", section_style),
            Paragraph(
                (
                    "Le présent contrat a pour objet l’embauche de l’Employé(e) par PrimeBank en qualité de :<br/>"
                    f"[{contract_type_name}]<br/>"
                    "L’Employé(e) exercera ses fonctions sous l’autorité hiérarchique de [Nom / Responsable]."
                ),
                body_style,
            ),
            Paragraph("Article 2 – Date d’entrée en fonction", section_style),
            Paragraph(
                (
                    f"Le contrat prend effet à compter du {start_date}.<br/>"
                    f"Date de fin prévue : {end_date}."
                ),
                body_style,
            ),
            Paragraph("Article 3 – Période d’essai", section_style),
            Paragraph(
                (
                    "Une période d’essai de [X mois] est prévue.<br/>"
                    "Elle pourra être renouvelée conformément aux dispositions légales en vigueur.<br/>"
                    "Pendant cette période, le contrat pourra être rompu par l’une ou l’autre des parties selon les modalités légales."
                ),
                body_style,
            ),
            Paragraph("Article 4 – Lieu de travail", section_style),
            Paragraph(
                (
                    "Le poste est basé à :<br/>"
                    "[Adresse du siège ou agence]<br/>"
                    "Le télétravail peut être autorisé conformément à la politique interne de PrimeBank."
                ),
                body_style,
            ),
            Paragraph("Article 5 – Durée du travail", section_style),
            Paragraph(
                (
                    f"La durée hebdomadaire de travail est fixée à : {weekly_hours}.<br/>"
                    "Les horaires sont définis selon le planning établi par l’entreprise.<br/>"
                    "Les heures supplémentaires éventuelles seront rémunérées ou récupérées conformément à la législation."
                ),
                body_style,
            ),
            Paragraph("Article 6 – Rémunération", section_style),
            Paragraph(
                (
                    "En contrepartie de ses fonctions, l’Employé(e) percevra :<br/>"
                    "Un salaire brut mensuel de : [XXX €]<br/>"
                    "Versé le [date] de chaque mois<br/>"
                    "Des primes ou bonus pourront être attribués selon la politique interne de PrimeBank."
                ),
                body_style,
            ),
            Paragraph("Article 7 – Congés payés", section_style),
            Paragraph(
                (
                    "L’Employé(e) bénéficie des congés payés légaux en vigueur.<br/>"
                    "Les demandes de congés devront être validées via le système interne de gestion du temps."
                ),
                body_style,
            ),
            Paragraph("Article 8 – Confidentialité", section_style),
            Paragraph(
                (
                    "L’Employé(e) s’engage à :<br/>"
                    "Respecter la confidentialité des données bancaires<br/>"
                    "Ne divulguer aucune information sensible<br/>"
                    "Respecter les obligations liées au RGPD<br/>"
                    "Cette obligation perdure après la fin du contrat."
                ),
                body_style,
            ),
            Paragraph("Article 9 – Protection des données personnelles (RGPD)", section_style),
            Paragraph(
                (
                    "PrimeBank collecte et traite les données personnelles de l’Employé(e) conformément à la réglementation en vigueur.<br/>"
                    "L’Employé(e) dispose d’un droit d’accès, de rectification et d’effacement de ses données."
                ),
                body_style,
            ),
            Paragraph("Article 10 – Outils et sécurité informatique", section_style),
            Paragraph(
                (
                    "L’Employé(e) s’engage à :<br/>"
                    "Utiliser les outils informatiques conformément aux politiques internes<br/>"
                    "Respecter les procédures de sécurité (authentification forte, VPN, etc.)<br/>"
                    "Ne pas partager ses identifiants"
                ),
                body_style,
            ),
            Paragraph("Article 11 – Résiliation", section_style),
            Paragraph(
                (
                    "Le contrat pourra être rompu selon les dispositions légales applicables.<br/>"
                    "Un préavis devra être respecté selon l’ancienneté et la législation."
                ),
                body_style,
            ),
            Paragraph("Article 12 – Convention collective", section_style),
            Paragraph(
                "Le présent contrat est soumis à la convention collective applicable au secteur bancaire.",
                body_style,
            ),
            Spacer(1, 12),
            Paragraph(f"Fait à {city}, le {today_str}", body_style),
            Paragraph("En deux exemplaires originaux.", body_style),
            Spacer(1, 12),
            Paragraph("Signature de l’Employeur", section_style),
            Paragraph("Nom : ____________________", body_style),
            Paragraph("Signature : ____________________", body_style),
            Spacer(1, 8),
            Paragraph("Signature de l’Employé(e)", section_style),
            Paragraph(f"Nom : {user_name}", body_style),
            Paragraph("Signature : ____________________", body_style),
        ]

        document.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename=contract_{contract.id}.pdf"
        response.write(pdf_data)
        return response
