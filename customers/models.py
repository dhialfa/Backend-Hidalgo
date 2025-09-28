
from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=200)
    identification = models.CharField(max_length=30)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    direction = models.CharField(max_length=250)
    location = models.CharField(max_length=200)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.identification})"
