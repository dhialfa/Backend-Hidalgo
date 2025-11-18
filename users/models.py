# users/models.py
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from core.models import BaseModel, TimeStampedModel  # te da active, created_at, updated_at

class ActiveUserManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(active=True)  # usa 'active' del BaseModel

class User(AbstractUser, BaseModel, TimeStampedModel):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)

    created_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="users_created"
    )
    updated_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="users_updated"
    )

    # ¡Importante!: mantener el manager de auth con get_by_natural_key
    objects = UserManager()
    active_objects = ActiveUserManager()

    def __str__(self):
        return self.username
