from django.db import models


class ContractType(models.Model):
    """
    Type de contrat configurable (CDI, CDD, Stage, Freelance…).
    """

    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)

    description = models.TextField(blank=True)

    # Permet de définir une règle métier dynamique
    requires_end_date = models.BooleanField(default=False)

    def __str__(self):
        return self.name
