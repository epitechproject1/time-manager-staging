from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .contract_type import ContractType

User = settings.AUTH_USER_MODEL


class Contract(models.Model):
    """
    Représente le contrat de travail d’un utilisateur.
    C’est la base légale qui définit la période et la charge horaire.
    """

    # 🔗 Utilisateur concerné par le contrat
    # Un utilisateur peut avoir plusieurs contrats dans le temps (historique)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contracts")

    # 🔗 Type de contrat (configurable en base : CDI, CDD, Stage…)
    contract_type = models.ForeignKey(
        ContractType, on_delete=models.PROTECT, related_name="contracts"
    )

    # 📅 Date de début du contrat
    start_date = models.DateField()

    # 📅 Date de fin (optionnelle selon le type de contrat)
    end_date = models.DateField(null=True, blank=True)

    # ⏱️ Nombre d’heures hebdomadaires prévues
    weekly_hours_target = models.DecimalField(max_digits=5, decimal_places=2)

    # 🕒 Date de création en base
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["contract_type"]),
        ]

    def clean(self):
        """
        Validation métier du contrat.
        """

        # Vérifie si le type de contrat exige une date de fin
        if self.contract_type.requires_end_date and not self.end_date:
            raise ValidationError("Ce type de contrat nécessite une date de fin.")

        # Vérifie la cohérence des dates
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("La date de fin doit être après la date de début.")

    def __str__(self):
        return f"{self.user} - {self.contract_type} ({self.start_date})"
