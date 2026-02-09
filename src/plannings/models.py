from django.conf import settings
from django.db import models


class PlanningType(models.TextChoices):
    SHIFT = "SHIFT", "Shift"
    LEAVE = "LEAVE", "Leave"
    EVENT = "EVENT", "Event"


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

    # temporaire tant que Team n'est pas livré
    team_id = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
