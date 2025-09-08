# subscriptions/models.py
from django.db import models
from django.core.exceptions import ValidationError


class PlanSubscription(models.Model):
    STATUS_CHOICES = (
        ("ACTIVA", "ACTIVA"),
        ("SUSPENDIDA", "SUSPENDIDA"),
        ("CANCELADA", "CANCELADA"),
    )

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    plan = models.ForeignKey(
        "plans.Plan",
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "subscriptions_plan_subscription"
        ordering = ["-start_date", "id"]
        constraints = [
            # (cliente, plan, fecha_inicio) único
            models.UniqueConstraint(
                fields=["customer", "plan", "start_date"],
                name="uniq_customer_plan_startdate",
            )
        ]
        indexes = [
            models.Index(fields=["customer", "plan", "start_date"], name="idx_subs_c_p_s"),
            models.Index(fields=["status"], name="idx_subs_status"),
        ]

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "end_date cannot be before start_date."})

    def __str__(self) -> str:
        return f"{self.customer_id} · {self.plan_id} · {self.start_date} ({self.status})"
