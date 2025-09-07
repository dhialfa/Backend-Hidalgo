from django.conf import settings
from django.db import models


class Technician(models.Model):
    # Guarda el nombre de columna como 'usuario_id' en la BD, pero el campo en Django es 'user'
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="technician",
        db_column="usuario_id",
    )
    phone = models.CharField(max_length=30, blank=True, null=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Technician"
        verbose_name_plural = "Technicians"
        indexes = [
            models.Index(fields=["active"]),
        ]

    def __str__(self):
        return f"{self.user} ({'active' if self.active else 'inactive'})"
