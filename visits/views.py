import os
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import viewsets, permissions, decorators, response, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError

from .models import Visit, Assessment, Evidence, TaskCompleted, MaterialUsed
from .serializers import (
    VisitSerializer, AssessmentSerializer, EvidenceSerializer,
    TaskCompletedSerializer, MaterialUsedSerializer
)

# Permite desactivar auth para pruebas locales (igual que en customers)
DISABLE_AUTH = os.getenv("DISABLE_AUTH", "0") == "1"


def _actor_or_none(request):
    u = getattr(request, "user", None)
    return u if (u and getattr(u, "is_authenticated", False)) else None


class _BaseAuthViewSet(viewsets.ModelViewSet):
    """
    Base que replica el patrón de customers:
    - Permisos dependientes de DISABLE_AUTH
    - Backends de filtros/búsqueda/ordenamiento
    """
    permission_classes = [permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Guarda actor (si el modelo tiene esos campos)
    def perform_create(self, serializer):
        actor = _actor_or_none(self.request)
        save_kwargs = {}
        for k in ("created_by", "updated_by"):
            if hasattr(serializer.Meta.model, k) and actor:
                save_kwargs[k] = actor
        serializer.save(**save_kwargs)

    def perform_update(self, serializer):
        actor = _actor_or_none(self.request)
        if hasattr(serializer.Meta.model, "updated_by") and actor:
            serializer.save(updated_by=actor)
        else:
            serializer.save()


# -------------------- Visits --------------------
class VisitViewSet(_BaseAuthViewSet):
    queryset = (
        Visit.objects.select_related("subscription", "user")
        .all()
        .order_by("-start", "id")
    )
    serializer_class = VisitSerializer
    filterset_fields = ["subscription", "user", "status", "start", "end"]
    search_fields = ["site_address", "notes", "cancel_reason"]
    ordering_fields = ["start", "end", "updated_at", "id"]
    ordering = ["-start", "id"]

    @decorators.action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def cancel(self, request, pk=None):
        """
        POST /api/visits/{id}/cancel/
        Body opcional: {"cancel_reason": "..."}
        """
        obj = self.get_object()
        reason = request.data.get("cancel_reason", "") or "Canceled"
        obj.status = "canceled"
        obj.cancel_reason = reason
        obj.save(update_fields=["status", "cancel_reason", "updated_at"])
        return response.Response({"detail": "Visit canceled"}, status=status.HTTP_200_OK)

    @decorators.action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def complete(self, request, pk=None):
        """
        POST /api/visits/{id}/complete/
        Opcional body: {"end": "2025-10-12T18:30:00Z"}
        """
        obj = self.get_object()
        end = request.data.get("end")
        obj.end = end or obj.end or timezone.now()
        obj.status = "completed"
        obj.save(update_fields=["status", "end", "updated_at"])
        return response.Response({"detail": "Visit completed"}, status=status.HTTP_200_OK)


# -------------------- Assessment --------------------
class AssessmentViewSet(_BaseAuthViewSet):
    queryset = Assessment.objects.select_related("visit").all().order_by("-created_at", "id")
    serializer_class = AssessmentSerializer
    filterset_fields = ["visit", "rating"]
    ordering_fields = ["created_at", "id"]
    ordering = ["-created_at", "id"]

    @decorators.action(
        detail=False,
        methods=["post"],
        url_path=r"upsert-by-visit/(?P<visit_id>\d+)",
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    @transaction.atomic
    def upsert_by_visit(self, request, visit_id=None):
        """
        POST /api/assessments/upsert-by-visit/<visit_id>/
        Crea o actualiza el Assessment de esa visita (OneToOne).
        """
        visit = get_object_or_404(Visit.objects, pk=visit_id)
        try:
            obj = Assessment.objects.get(visit=visit)
            ser = AssessmentSerializer(obj, data=request.data, partial=True, context={"request": request})
        except Assessment.DoesNotExist:
            data = dict(request.data)
            data["visit"] = visit.id
            ser = AssessmentSerializer(data=data, context={"request": request})
        ser.is_valid(raise_exception=True)

        actor = _actor_or_none(request)
        save_kwargs = {}
        if hasattr(Assessment, "updated_by") and actor:
            save_kwargs["updated_by"] = actor
        if hasattr(Assessment, "created_by") and actor and not getattr(ser.instance, "pk", None):
            save_kwargs["created_by"] = actor

        obj = ser.save(**save_kwargs)
        out = AssessmentSerializer(obj, context={"request": request})
        return response.Response(out.data, status=status.HTTP_200_OK)


# -------------------- Evidence --------------------
class EvidenceViewSet(_BaseAuthViewSet):
    queryset = Evidence.objects.select_related("visit").all().order_by("-subido_en", "id")
    serializer_class = EvidenceSerializer
    filterset_fields = ["visit"]
    ordering_fields = ["subido_en", "id"]
    ordering = ["-subido_en", "id"]

    @decorators.action(
        detail=False,
        methods=["get", "post"],
        url_path=r"by-visit/(?P<visit_id>\d+)",
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def by_visit(self, request, visit_id=None):
        """
        GET  /api/evidences/by-visit/<visit_id>/
        POST /api/evidences/by-visit/<visit_id>/   (no envíes "visit" en el body)
        """
        visit = get_object_or_404(Visit.objects, pk=visit_id)

        if request.method.lower() == "get":
            qs = self.get_queryset().filter(visit=visit)
            page = self.paginate_queryset(qs)
            if page is not None:
                ser = EvidenceSerializer(page, many=True, context={"request": request})
                return self.get_paginated_response(ser.data)
            ser = EvidenceSerializer(qs, many=True, context={"request": request})
            return response.Response(ser.data, status=status.HTTP_200_OK)

        ser = EvidenceSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        actor = _actor_or_none(request)
        save_kwargs = {"visit": visit}
        for k in ("created_by", "updated_by"):
            if hasattr(Evidence, k) and actor:
                save_kwargs[k] = actor
        obj = ser.save(**save_kwargs)
        out = EvidenceSerializer(obj, context={"request": request})
        return response.Response(out.data, status=status.HTTP_201_CREATED)


# -------------------- TaskCompleted --------------------
class TaskCompletedViewSet(_BaseAuthViewSet):
    queryset = TaskCompleted.objects.select_related("visit", "plan_task").all().order_by("id")
    serializer_class = TaskCompletedSerializer
    filterset_fields = ["visit", "plan_task", "completada"]
    ordering_fields = ["id", "hours"]
    ordering = ["id"]

    @decorators.action(
        detail=False,
        methods=["get", "post"],
        url_path=r"by-visit/(?P<visit_id>\d+)",
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def by_visit(self, request, visit_id=None):
        """
        GET  /api/task-completed/by-visit/<visit_id>/
        POST /api/task-completed/by-visit/<visit_id>/   (no envíes "visit" en el body)
        """
        visit = get_object_or_404(Visit.objects, pk=visit_id)

        if request.method.lower() == "get":
            qs = self.get_queryset().filter(visit=visit).order_by("id")
            page = self.paginate_queryset(qs)
            if page is not None:
                ser = TaskCompletedSerializer(page, many=True, context={"request": request})
                return self.get_paginated_response(ser.data)
            ser = TaskCompletedSerializer(qs, many=True, context={"request": request})
            return response.Response(ser.data, status=status.HTTP_200_OK)

        ser = TaskCompletedSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        actor = _actor_or_none(request)
        save_kwargs = {"visit": visit}
        for k in ("created_by", "updated_by"):
            if hasattr(TaskCompleted, k) and actor:
                save_kwargs[k] = actor
        obj = ser.save(**save_kwargs)
        out = TaskCompletedSerializer(obj, context={"request": request})
        return response.Response(out.data, status=status.HTTP_201_CREATED)

    @decorators.action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def toggle(self, request, pk=None):
        """
        POST /api/task-completed/{id}/toggle/
        Invierte el booleano 'completada'.
        """
        obj = self.get_object()
        obj.completada = not bool(obj.completada)
        obj.save(update_fields=["completada"])
        return response.Response({"completada": obj.completada}, status=status.HTTP_200_OK)


# -------------------- MaterialUsed --------------------
class MaterialUsedViewSet(_BaseAuthViewSet):
    queryset = MaterialUsed.objects.select_related("visit").all().order_by("id")
    serializer_class = MaterialUsedSerializer
    filterset_fields = ["visit"]
    ordering_fields = ["unit_cost", "id"]
    ordering = ["id"]

    @decorators.action(
        detail=False,
        methods=["get", "post"],
        url_path=r"by-visit/(?P<visit_id>\d+)",
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def by_visit(self, request, visit_id=None):
        """
        GET  /api/material-used/by-visit/<visit_id>/
        POST /api/material-used/by-visit/<visit_id>/   (no envíes "visit" en el body)
        """
        visit = get_object_or_404(Visit.objects, pk=visit_id)

        if request.method.lower() == "get":
            qs = self.get_queryset().filter(visit=visit).order_by("id")
            page = self.paginate_queryset(qs)
            if page is not None:
                ser = MaterialUsedSerializer(page, many=True, context={"request": request})
                return self.get_paginated_response(ser.data)
            ser = MaterialUsedSerializer(qs, many=True, context={"request": request})
            return response.Response(ser.data, status=status.HTTP_200_OK)

        ser = MaterialUsedSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        actor = _actor_or_none(request)
        save_kwargs = {"visit": visit}
        for k in ("created_by", "updated_by"):
            if hasattr(MaterialUsed, k) and actor:
                save_kwargs[k] = actor
        obj = ser.save(**save_kwargs)
        out = MaterialUsedSerializer(obj, context={"request": request})
        return response.Response(out.data, status=status.HTTP_201_CREATED)
