from django.conf import settings
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

    planning_type = models.CharField(
        max_length=20, choices=PlanningType.choices, default=PlanningType.SHIFT
    )
    work_mode = models.CharField(
        max_length=20, choices=WorkMode.choices, default=WorkMode.ONSITE
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="plannings",
        null=True,
        blank=True,
    )

    # ✅ FK vers Teams (nouveau modèle)
    team = models.ForeignKey(
        "teams.Teams",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="plannings",
    )


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_datetime"]

    def __str__(self) -> str:
        return f"{self.title} ({self.start_datetime} -> {self.end_datetime})"
