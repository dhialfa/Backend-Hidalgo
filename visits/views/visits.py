# visits/views/visits.py
import os
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, decorators, response, status, filters
from rest_framework.exceptions import ValidationError

from visits.validations import (
    validate_visit_dates,
    ensure_active_user,
    ensure_active_subscription,
)

from ..models import Visit, Assessment  # Assessment usado en acción by-visit
from ..serializers import VisitSerializer, AssessmentSerializer  # for by-visit upsert

# ---------- Auth toggle ----------
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

    # --- hooks DRF ---
    def perform_create(self, serializer):
        validate_visit_dates(serializer)
        ensure_active_user(serializer)
        ensure_active_subscription(serializer)

        actor = _actor_or_none(self.request)
        save_kwargs = {}
        if actor:
            save_kwargs.update(created_by=actor, updated_by=actor)
        serializer.save(**save_kwargs)

    def perform_update(self, serializer):
        instance = self.get_object()
        validate_visit_dates(serializer, instance=instance)
        ensure_active_user(serializer, instance=instance)
        ensure_active_subscription(serializer, instance=instance)

        actor = _actor_or_none(self.request)
        if actor:
            serializer.save(updated_by=actor)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        instance.delete()  # borrado lógico

    # ---------- acciones ----------
    @decorators.action(
        detail=True, methods=["post"],
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def restore(self, request, pk=None):
        obj = self.get_object()
        obj.active = True
        obj.save(update_fields=["active"])
        return response.Response({"detail": "Visit restored"}, status=status.HTTP_200_OK)

    @decorators.action(
        detail=False,
        methods=["get", "post"],
        url_path=r"by-subscription/(?P<subscription_id>\d+)",
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def by_subscription(self, request, subscription_id=None):
        """
        GET  /api/visit/by-subscription/<subscription_id>/
        POST /api/visit/by-subscription/<subscription_id>/  (body SIN 'subscription')
        """
        from plans.models import PlanSubscription
        subscription = get_object_or_404(PlanSubscription.objects, pk=subscription_id)

        # bloquear suscripciones inactivas
        if not getattr(subscription, "active", True):
            raise ValidationError({"subscription": "La suscripción está inactiva."})

        if request.method.lower() == "get":
            qs = (
                Visit.active_objects
                .filter(subscription=subscription)
                .select_related("subscription", "user")
                .order_by("-start", "id")
            )
            page = self.paginate_queryset(qs)
            if page is not None:
                ser = VisitSerializer(page, many=True, context={"request": request})
                return self.get_paginated_response(ser.data)
            ser = VisitSerializer(qs, many=True, context={"request": request})
            return response.Response(ser.data, status=status.HTTP_200_OK)

        # POST
        ser = VisitSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)

        validate_visit_dates(ser)
        ensure_active_user(ser)
        ensure_active_subscription(subscription_override=subscription)

        actor = _actor_or_none(request)
        save_kwargs = {"subscription": subscription}
        if actor:
            save_kwargs.update(created_by=actor, updated_by=actor)

        obj = ser.save(**save_kwargs)
        out = VisitSerializer(obj, context={"request": request})
        return response.Response(out.data, status=status.HTTP_201_CREATED)

    @decorators.action(
        detail=False,
        methods=["get"],
        url_path=r"by-user/(?P<user_id>\d+)",
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def by_user(self, request, user_id=None):
        qs = (
            Visit.active_objects
            .filter(user_id=user_id)
            .select_related("subscription", "user")
            .order_by("-start", "id")
        )
        status_q = request.query_params.get("status")
        if status_q:
            qs = qs.filter(status=status_q)

        page = self.paginate_queryset(qs)
        if page is not None:
            ser = VisitSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(ser.data)
        ser = VisitSerializer(qs, many=True, context={"request": request})
        return response.Response(ser.data, status=status.HTTP_200_OK)

    @decorators.action(
        detail=False,
        methods=["get"],
        url_path=r"by-customer/(?P<customer_id>\d+)",
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def by_customer(self, request, customer_id=None):
        qs = (
            Visit.active_objects
            .filter(subscription__customer_id=customer_id)
            .select_related("subscription", "user")
            .order_by("-start", "id")
        )
        status_q = request.query_params.get("status")
        if status_q:
            qs = qs.filter(status=status_q)

        page = self.paginate_queryset(qs)
        if page is not None:
            ser = VisitSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(ser.data)
        ser = VisitSerializer(qs, many=True, context={"request": request})
        return response.Response(ser.data, status=status.HTTP_200_OK)

    # Acciones rápidas de estado
    @decorators.action(
        detail=True, methods=["post"],
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def start_now(self, request, pk=None):
        obj = self.get_object()
        if not obj.start:
            obj.start = timezone.now()
        obj.status = Visit.Status.IN_PROGRESS
        obj.save(update_fields=["start", "status"])
        return response.Response({"detail": "Visit started"}, status=status.HTTP_200_OK)

    @decorators.action(
        detail=True, methods=["post"],
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def complete(self, request, pk=None):
        obj = self.get_object()
        if not obj.end:
            obj.end = timezone.now()
        obj.status = Visit.Status.COMPLETED
        obj.save(update_fields=["end", "status"])
        return response.Response({"detail": "Visit completed"}, status=status.HTTP_200_OK)

    @decorators.action(
        detail=True, methods=["post"],
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def cancel(self, request, pk=None):
        obj = self.get_object()
        reason = request.data.get("cancel_reason", "")
        obj.cancel_reason = reason
        obj.status = Visit.Status.CANCELED
        obj.save(update_fields=["cancel_reason", "status"])
        return response.Response({"detail": "Visit cancelled"}, status=status.HTTP_200_OK)
