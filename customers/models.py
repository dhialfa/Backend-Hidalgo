
from django.db import models, transaction
from core.models import BaseModel, TimeStampedModel

class Customer(BaseModel, TimeStampedModel):
    name = models.CharField(max_length=255)
    identification = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    direction = models.CharField(max_length=255, blank=True, null=True)

    @transaction.atomic
    def delete(self, using=None, keep_parents=False):
        """
        Soft delete del Customer y cascada lógica a:
        - PlanSubscription del cliente
        - Visit de esas suscripciones
        - Assessment, Evidence, TaskCompleted, MaterialUsed ligados a esas visitas
        - (Opcional) CustomerContact del cliente
        """
        # 1) Marca al propio customer como inactivo (usa BaseModel.delete)
        super().delete(using=using, keep_parents=keep_parents)

        # 2) Imports locales para evitar ciclos
        from plans.models import PlanSubscription
        from visits.models import Visit, Assessment, Evidence, TaskCompleted, MaterialUsed
        from customers.models import CustomerContact

        # 3) Soft-delete en cascada (bulk updates, eficientes)
        #   a) Suscripciones del cliente
        PlanSubscription.objects.filter(customer_id=self.pk, active=True).update(active=False)

        #   b) Visitas de esas suscripciones
        Visit.objects.filter(subscription__customer_id=self.pk, active=True).update(active=False)

        #   c) Hijos de visitas
        Assessment.objects.filter(visit__subscription__customer_id=self.pk, active=True).update(active=False)
        Evidence.objects.filter(visit__subscription__customer_id=self.pk, active=True).update(active=False)
        TaskCompleted.objects.filter(visit__subscription__customer_id=self.pk, active=True).update(active=False)
        MaterialUsed.objects.filter(visit__subscription__customer_id=self.pk, active=True).update(active=False)

        #   d) (Opcional) Contactos del cliente
        CustomerContact.objects.filter(customer_id=self.pk, active=True).update(active=False)
        
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