from django.db import models
from django.conf import settings

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(active=True)

class BaseModel(models.Model):
    active = models.BooleanField(default=True)

    # Managers
    objects = models.Manager()         # todos (activos e inactivos)
    active_objects = ActiveManager()   # solo activos

    class Meta:
        abstract = True

    # Soft delete: marca como inactivo en lugar de borrar
    def delete(self, using=None, keep_parents=False):
        self.active = False
        self.save(update_fields=["active"])

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",   # ej: customercontact_created
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated",   # ej: customercontact_updated
    )

    class Meta:
        abstract = True
