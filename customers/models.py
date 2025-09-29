
from django.db import models
from core.models import BaseModel, TimeStampedModel

class Customer(BaseModel, TimeStampedModel):
    name = models.CharField(max_length=200)
    identification = models.CharField(max_length=30)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    direction = models.CharField(max_length=250)
    location = models.CharField(max_length=200)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.identification})"

class CustomerContact(BaseModel, TimeStampedModel):
    customer = models.ForeignKey(
        "Customer",  
        on_delete=models.CASCADE,
        related_name="contacts"
    )
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    is_main = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.customer})"