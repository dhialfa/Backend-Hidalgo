from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    class Roles(models.TextChoices):
        ADMINISTRADOR = "ADMIN", "Administrador"
        TECNICO = "TECNICO", "Técnico"

    rol = models.CharField(
        max_length=10,
        choices=Roles.choices,
        default=Roles.ADMINISTRADOR,
    )

    telefono = models.CharField(max_length=30, blank=True)

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"
