from django.db import models


class WeekPattern(models.Model):
    """
    Représente une semaine type.
    Sert de base pour construire des plannings réutilisables.
    """

    name = models.CharField(max_length=200, unique=True)

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
