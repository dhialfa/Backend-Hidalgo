from django.db import models
from customers.models import Customer
from core.models import BaseModel, TimeStampedModel

class Plan(BaseModel, TimeStampedModel):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

class PlanTask(BaseModel, TimeStampedModel):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="tasks")
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["plan_id", "name"]
        constraints = []


    def __str__(self) -> str:
        return f"{self.plan.name} . {self.name}"

class PlanSubscription(BaseModel, TimeStampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    start_date = models.DateField()
    status = models.CharField(max_length=10)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self) -> str:
        return f"{self.customer.name} → {self.plan.name} ({self.status})"
