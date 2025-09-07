# accounts/models.py (DEFINITIVO)
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (("ADMIN", "ADMIN"), ("TECHNICIAN", "TECHNICIAN"))
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=30, blank=True, null=True)
