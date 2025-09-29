from django.db import models
from django.conf import settings
from plans.models import PlanSubscription, PlanTask

class Visit(models.Model):
    subscription = models.ForeignKey(
        PlanSubscription, on_delete=models.CASCADE, related_name="visits"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="performed_visits"
    )
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12)  # e.g. scheduled, done, canceled
    site_address = models.CharField(max_length=250, blank=True)
    notes = models.TextField(blank=True)
    cancel_reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start"]

    def __str__(self) -> str:
        return f"Visit {self.id} - {self.subscription} - {self.start:%Y-%m-%d %H:%M}"

class Assessment(models.Model):
    visit = models.OneToOneField(Visit, on_delete=models.CASCADE, related_name="assessment")
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Assessment for visit {self.visit_id}"

class Evidence(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="evidences")
    file = models.FileField(upload_to="evidence/")
    description = models.CharField(max_length=200, blank=True)
    subido_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-subido_en"]

    def __str__(self) -> str:
        return f"Evidence {self.id} for visit {self.visit_id}"

class TaskCompleted(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="tasks_completed")
    plan_task = models.ForeignKey(PlanTask, on_delete=models.PROTECT, related_name="completions")
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    hours = models.PositiveIntegerField(default=0)
    completada = models.BooleanField(default=False)

    class Meta:
        ordering = ["visit_id", "id"]

    def __str__(self) -> str:
        return f"{self.name} - visit {self.visit_id}"

class MaterialUsed(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name="materials_used")
    description = models.CharField(max_length=150)
    unit = models.CharField(max_length=30, blank=True)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self) -> str:
        return f"{self.description} - visit {self.visit_id}"
