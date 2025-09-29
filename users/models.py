from django.contrib.auth.models import AbstractUser
from django.db import models
from core.models import BaseModel, TimeStampedModel

class User(AbstractUser, BaseModel, TimeStampedModel):
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.username
