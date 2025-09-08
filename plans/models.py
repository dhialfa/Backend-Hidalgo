# plans/models.py
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models


class Plan(models.Model):
    PERIODICITY_CHOICES = (
        ("MENSUAL", "MENSUAL"),
        ("BIMESTRAL", "BIMESTRAL"),
        ("TRIMESTRAL", "TRIMESTRAL"),
        ("SEMESTRAL", "SEMESTRAL"),
        ("ANUAL", "ANUAL"),
    )

    name = models.CharField(max_length=120, db_index=True)
    description = models.TextField(blank=True, null=True)
    periodicity = models.CharField(max_length=12, choices=PERIODICITY_CHOICES, db_index=True)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["periodicity"]),
        ]

    def __str__(self):
        return self.name


class PlanTask(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="tasks")
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["plan_id", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "name"], name="uniq_task_name_per_plan"
            )
        ]
        indexes = [
            models.Index(fields=["plan", "name"], name="idx_plan_task_plan_name"),
        ]

    def __str__(self):
        return f"{self.plan_id} · {self.name}"
