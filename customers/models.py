from django.db import models
from django.db.models import Q


class Customer(models.Model):
    legal_name = models.CharField(max_length=200, db_index=True)
    identification = models.CharField(max_length=30, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True, null=True)
    address = models.CharField(max_length=250, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["legal_name"]),
        ]
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return f"{self.legal_name} ({self.identification})"


class CustomerContact(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        constraints = [
            # Ensure only one primary contact per customer
            models.UniqueConstraint(
                fields=["customer"],
                condition=Q(is_primary=True),
                name="uniq_primary_contact_per_customer",
            )
        ]
        indexes = [
            models.Index(fields=["customer", "is_primary"]),
        ]
        verbose_name = "Customer Contact"
        verbose_name_plural = "Customer Contacts"

    def __str__(self):
        status = "primary" if self.is_primary else "secondary"
        return f"{self.name} ({status})"