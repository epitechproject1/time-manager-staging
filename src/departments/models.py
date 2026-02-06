from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    director = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name} - {self.director}"
