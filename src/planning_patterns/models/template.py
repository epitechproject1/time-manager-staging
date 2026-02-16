from django.db import models

from .week_pattern import WeekPattern


class PlanningTemplate(models.Model):
    """
    Modèle de planning réutilisable.
    Sert par exemple pour appliquer rapidement un planning à un contrat.
    """

    name = models.CharField(max_length=200, unique=True)

    # 🔗 Le template se base sur une semaine type
    week_pattern = models.ForeignKey(
        WeekPattern, on_delete=models.PROTECT, related_name="templates"
    )

    # Nombre d’heures hebdomadaires prévues (optionnel)
    weekly_hours_target = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
