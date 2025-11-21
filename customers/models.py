
from django.db import models, transaction
from core.models import BaseModel, TimeStampedModel

# customers/models.py
from django.db import models, transaction
# ...

# customers/models.py
from django.db import models, transaction
# ...

class Customer(BaseModel, TimeStampedModel):
    name = models.CharField(max_length=255)
    identification = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    direction = models.CharField(max_length=255, blank=True, null=True)

    @transaction.atomic
    def soft_delete_cascade(self):
        """
        Soft-delete en cascada:
        - PlanSubscription del cliente
        - Visit de esas suscripciones
        - Assessment, Evidence, TaskCompleted, MaterialUsed ligados a esas visitas
        - CustomerContact del cliente
        """
        from plans.models import PlanSubscription
        from visits.models import Visit, Assessment, Evidence, TaskCompleted, MaterialUsed
        from customers.models import CustomerContact

        # a) Suscripciones del cliente
        PlanSubscription.objects.filter(
            customer_id=self.pk,
            active=True,
        ).update(active=False)

        # b) Visitas de esas suscripciones
        Visit.objects.filter(
            subscription__customer_id=self.pk,
            active=True,
        ).update(active=False)

        # c) Hijos de visitas
        Assessment.objects.filter(
            visit__subscription__customer_id=self.pk,
            active=True,
        ).update(active=False)
        Evidence.objects.filter(
            visit__subscription__customer_id=self.pk,
            active=True,
        ).update(active=False)
        TaskCompleted.objects.filter(
            visit__subscription__customer_id=self.pk,
            active=True,
        ).update(active=False)
        MaterialUsed.objects.filter(
            visit__subscription__customer_id=self.pk,
            active=True,
        ).update(active=False)

        # d) Contactos del cliente
        CustomerContact.objects.filter(
            customer_id=self.pk,
            active=True,
        ).update(active=False)

    @transaction.atomic
    def delete(self, using=None, keep_parents=False):
        """
        Soft delete del Customer y cascada lógica.
        """
        # 1) Marca al propio customer como inactivo (usa BaseModel.delete)
        super().delete(using=using, keep_parents=keep_parents)

        # 2) Soft-delete en cascada
        self.soft_delete_cascade()


    @transaction.atomic
    def delete(self, using=None, keep_parents=False):
        """
        Soft delete del Customer y cascada lógica.
        """
        # 1) Marca al propio customer como inactivo (usa BaseModel.delete)
        super().delete(using=using, keep_parents=keep_parents)

        # 2) Cascada lógica reutilizable
        self.soft_delete_cascade()

        
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