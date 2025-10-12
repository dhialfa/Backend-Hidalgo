# visits/models.py
from django.conf import settings
from django.db import models


# --------- Base abstracta con auditoría ---------
class TimeStampedBy(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_updated",
    )

    class Meta:
        abstract = True


# --------- Visit ---------
class Visit(TimeStampedBy):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        CANCELED = "canceled", "Canceled"

    subscription = models.ForeignKey(
        "plans.PlanSubscription",
        on_delete=models.CASCADE,
        related_name="visits",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="visits",
    )

    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SCHEDULED)
    site_address = models.CharField(max_length=250, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    cancel_reason = models.CharField(max_length=200, blank=True, default="")

    def __str__(self):
        return f"Visit #{self.pk} — {self.get_status_display()}"

    class Meta:
        ordering = ["-start", "id"]


# --------- Assessment (1:1 con Visit) ---------
class Assessment(TimeStampedBy):
    visit = models.OneToOneField(
        Visit, on_delete=models.CASCADE, related_name="assessment"
    )
    rating = models.PositiveSmallIntegerField(default=0)
    comment = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Assessment for visit {self.visit_id} ({self.rating})"

    class Meta:
        ordering = ["-created_at", "id"]


# --------- Evidence ---------
def evidence_upload_to(instance, filename: str) -> str:
    # puedes ajustar esta ruta a tu gusto
    return f"evidences/{instance.visit_id}/{filename}"


class Evidence(TimeStampedBy):
    visit = models.ForeignKey(
        Visit, on_delete=models.CASCADE, related_name="evidences"
    )
    file = models.FileField(upload_to=evidence_upload_to, null=True, blank=True)
    description = models.CharField(max_length=200, blank=True, default="")
    # En el diagrama existe "subido_en". Lo mantenemos porque tus vistas lo usan.
    subido_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evidence #{self.pk} for visit {self.visit_id}"

    class Meta:
        ordering = ["-subido_en", "id"]


# --------- TaskCompleted ---------
class TaskCompleted(TimeStampedBy):
    visit = models.ForeignKey(
        Visit, on_delete=models.CASCADE, related_name="tasks_completed"
    )
    plan_task = models.ForeignKey(
        "plans.PlanTask", on_delete=models.CASCADE, related_name="completions"
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, default="")
    hours = models.PositiveIntegerField(default=0)
    completada = models.BooleanField(default=False)

    def __str__(self):
        return f"TaskCompleted #{self.pk} ({'✓' if self.completada else '✗'})"

    class Meta:
        ordering = ["id"]


# --------- MaterialUsed ---------
class MaterialUsed(TimeStampedBy):
    visit = models.ForeignKey(
        Visit, on_delete=models.CASCADE, related_name="materials_used"
    )
    description = models.CharField(max_length=150)
    unit = models.CharField(max_length=30, blank=True, default="")
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"MaterialUsed #{self.pk} for visit {self.visit_id}"

    class Meta:
        ordering = ["id"]
