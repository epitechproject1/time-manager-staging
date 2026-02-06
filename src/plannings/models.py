from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class PlanningType(models.TextChoices):
    SHIFT = "SHIFT", "Shift"
    MEETING = "MEETING", "Meeting"
    PTO = "PTO", "Paid time off"


class WorkMode(models.TextChoices):
    ONSITE = "ONSITE", "On-site"
    REMOTE = "REMOTE", "Remote"
    HYBRID = "HYBRID", "Hybrid"


class Planning(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    planning_type = models.CharField(max_length=20, choices=PlanningType.choices)
    work_mode = models.CharField(max_length=20, choices=WorkMode.choices)

    # user_id existe dans le diagramme
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="plannings",
    )

    # team_id existe dans le diagramme, mais l'app teams n'est pas encore dispo
    team_id = models.BigIntegerField(null=True, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.start_datetime and self.end_datetime and self.end_datetime <= self.start_datetime:
            raise ValidationError({"end_datetime": "end_datetime must be after start_datetime"})

        if not self.user and not self.team_id:
            raise ValidationError("Planning must be linked to a user or a team_id")

    def __str__(self):
        return self.title
