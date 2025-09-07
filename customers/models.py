# customers/models.py
from django.db import models
from django.db.models import Q


class Cliente(models.Model):
    nombre_legal = models.CharField(max_length=200, db_index=True)
    identificacion = models.CharField(max_length=30, unique=True)
    correo = models.EmailField()
    telefono = models.CharField(max_length=30, blank=True, null=True)
    direccion = models.CharField(max_length=250, blank=True, null=True)
    ubicacion = models.CharField(max_length=200, blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["nombre_legal"]),
        ]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return f"{self.nombre_legal} ({self.identificacion})"


class ContactoCliente(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="contactos",
    )
    nombre = models.CharField(max_length=120)
    correo = models.EmailField()
    telefono = models.CharField(max_length=30, blank=True, null=True)
    es_principal = models.BooleanField(default=False)

    class Meta:
        constraints = [
            # Solo un contacto principal por cliente
            models.UniqueConstraint(
                fields=["cliente"],
                condition=Q(es_principal=True),
                name="uniq_principal_por_cliente",
            )
        ]
        indexes = [
            models.Index(fields=["cliente", "es_principal"]),
        ]
        verbose_name = "Contacto de cliente"
        verbose_name_plural = "Contactos de cliente"

    def __str__(self):
        estado = "principal" if self.es_principal else "secundario"
        return f"{self.nombre} ({estado})"
