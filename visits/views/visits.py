# visits/views/visits.py
import os
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, decorators, response, status, filters
from rest_framework.exceptions import ValidationError

from visits.utils import send_visit_completed_email_async
from visits.validations import (
    validate_visit_dates,
    ensure_active_user,
    ensure_active_subscription,
)

from ..models import Visit, Assessment
from ..serializers import VisitSerializer, AssessmentSerializer

DISABLE_AUTH = os.getenv("DISABLE_AUTH", "0") == "1"


def _actor_or_none(request):
  u = getattr(request, "user", None)
  return u if (u and getattr(u, "is_authenticated", False)) else None


class VisitViewSet(viewsets.ModelViewSet):
  queryset = (
    Visit.active_objects
    .select_related("subscription", "user")
    .prefetch_related("evidences", "tasks_completed", "materials_used")
    .all()
    .order_by("-start", "id")
  )
  serializer_class = VisitSerializer
  permission_classes = [permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated]
  filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
  filterset_fields = ["status", "subscription", "user", "start"]
  search_fields = [
    "notes",
    "site_address",
    "cancel_reason",
    "subscription__notes",
    "subscription__customer__name",
    "subscription__customer__identification",
  ]
  ordering_fields = ["start", "end", "status", "id", "created_at", "updated_at"]
  ordering = ["-start", "id"]

  def get_queryset(self):
    qs = super().get_queryset()
    sub_id = self.request.query_params.get("subscription")
    user_id = self.request.query_params.get("user")
    status_q = self.request.query_params.get("status")
    if sub_id:
      qs = qs.filter(subscription_id=sub_id)
    if user_id:
      qs = qs.filter(user_id=user_id)
    if status_q:
      qs = qs.filter(status=status_q)
    return qs

  # --- create ---
  def perform_create(self, serializer):
    validate_visit_dates(serializer)
    ensure_active_user(serializer)
    ensure_active_subscription(serializer)

    actor = _actor_or_none(self.request)
    save_kwargs = {}
    if actor:
      save_kwargs.update(created_by=actor, updated_by=actor)
    serializer.save(**save_kwargs)

  # --- update (PUT/PATCH) ---
  def perform_update(self, serializer):
    instance = self.get_object()
    old_status = instance.status

    validate_visit_dates(serializer, instance=instance)
    ensure_active_user(serializer, instance=instance)
    ensure_active_subscription(serializer, instance=instance)

    actor = _actor_or_none(self.request)
    if actor:
      serializer.save(updated_by=actor)
    else:
      serializer.save()

    instance.refresh_from_db()
    if old_status != instance.status and instance.status == Visit.Status.COMPLETED:
      send_visit_completed_email_async(instance)

  # ================= ACCIONES PERSONALIZADAS =================

  @decorators.action(
    detail=True,
    methods=["post"],
    permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
  )
  def start_now(self, request, pk=None):
    """
    Marca la visita como 'in_progress'. Si no tiene start, lo fija a ahora.
    """
    obj = self.get_object()

    if obj.status == Visit.Status.CANCELED:
      return response.Response(
        {"detail": "No se puede iniciar una visita cancelada"},
        status=status.HTTP_400_BAD_REQUEST,
      )

    if not obj.start:
      obj.start = timezone.now()
    obj.status = Visit.Status.IN_PROGRESS
    obj.save(update_fields=["start", "status"])

    return response.Response({"detail": "Visit started"}, status=status.HTTP_200_OK)

  @decorators.action(
    detail=True,
    methods=["post"],
    permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
  )
  def complete(self, request, pk=None):
    """
    Marca la visita como 'completed' y dispara el correo al cliente.
    """
    obj = self.get_object()

    # si no tiene end, se cierra ahora
    if not obj.end:
      obj.end = timezone.now()
    obj.status = Visit.Status.COMPLETED
    obj.save(update_fields=["end", "status"])

    # dispara correo asíncrono
    send_visit_completed_email_async(obj)

    return response.Response({"detail": "Visit completed"}, status=status.HTTP_200_OK)

  @decorators.action(
    detail=True,
    methods=["post"],
    permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
  )
  def cancel(self, request, pk=None):
    """
    Cancela la visita, guardando el motivo si viene en el body.
    """
    obj = self.get_object()
    reason = (request.data.get("cancel_reason") or "").strip()

    obj.status = Visit.Status.CANCELED
    obj.cancel_reason = reason
    # si quieres cerrar la visita al cancelar:
    if not obj.end:
      obj.end = timezone.now()

    obj.save(update_fields=["status", "cancel_reason", "end"])

    return response.Response({"detail": "Visit canceled"}, status=status.HTTP_200_OK)

  @decorators.action(
    detail=True,
    methods=["post"],
    permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
  )
  def restore(self, request, pk=None):
    """
    Vuelve a poner la visita en 'scheduled' y limpia el motivo de cancelación.
    """
    obj = self.get_object()
    obj.status = Visit.Status.SCHEDULED
    obj.cancel_reason = ""
    obj.save(update_fields=["status", "cancel_reason"])
    return response.Response({"detail": "Visit restored"}, status=status.HTTP_200_OK)


# Si también usas Assessment, lo dejo como estaba (ajusta según tu proyecto):

class AssessmentViewSet(viewsets.ModelViewSet):
  queryset = Assessment.objects.all().order_by("-created_at", "id")
  serializer_class = AssessmentSerializer
  permission_classes = [permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated]

  def perform_create(self, serializer):
    actor = _actor_or_none(self.request)
    if actor:
      serializer.save(created_by=actor, updated_by=actor)
    else:
      serializer.save()

  def perform_update(self, serializer):
    actor = _actor_or_none(self.request)
    if actor:
      serializer.save(updated_by=actor)
    else:
      serializer.save()
