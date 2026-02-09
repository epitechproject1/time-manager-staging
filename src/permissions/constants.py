from django.db import models


class PermissionType(models.TextChoices):
    READ = "READ", "Read"
    WRITE = "WRITE", "Write"
    APPROVE = "APPROVE", "Approve"
    ADMIN = "ADMIN", "Admin"
