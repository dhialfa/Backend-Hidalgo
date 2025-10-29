# visits/views/tasks_completed.py
import os
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, decorators, response, status, filters

from ..models import Visit, TaskCompleted
from ..serializers import TaskCompletedSerializer

DISABLE_AUTH = os.getenv("DISABLE_AUTH", "0") == "1"

def _actor_or_none(request):
    u = getattr(request, "user", None)
    return u if (u and getattr(u, "is_authenticated", False)) else None


class TaskCompletedViewSet(viewsets.ModelViewSet):
    queryset = (
        TaskCompleted.active_objects
        .select_related("visit", "plan_task")
        .all()
        .order_by("id")
    )
    serializer_class = TaskCompletedSerializer
    permission_classes = [permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["visit", "plan_task", "completada"]
    search_fields = ["name", "description", "visit__notes", "plan_task__name"]
    ordering_fields = ["hours", "id", "created_at", "updated_at"]
    ordering = ["id"]

    def perform_create(self, serializer):
        actor = _actor_or_none(self.request)
        serializer.save(**({"created_by": actor, "updated_by": actor} if actor else {}))

    def perform_update(self, serializer):
        actor = _actor_or_none(self.request)
        serializer.save(**({"updated_by": actor} if actor else {}))

    def perform_destroy(self, instance):
        instance.delete()

    @decorators.action(detail=True, methods=["post"], permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated])
    def restore(self, request, pk=None):
        obj = self.get_object()
        obj.active = True
        obj.save(update_fields=["active"])
        return response.Response({"detail": "TaskCompleted restored"}, status=status.HTTP_200_OK)

    @decorators.action(detail=False, methods=["get", "post"], url_path=r"by-visit/(?P<visit_id>\d+)",
                       permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated])
    def by_visit(self, request, visit_id=None):
        visit = get_object_or_404(Visit.objects, pk=visit_id)

        if request.method.lower() == "get":
            qs = (TaskCompleted.active_objects
                  .filter(visit=visit)
                  .select_related("plan_task")
                  .order_by("id"))
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
        if actor:
            save_kwargs.update(created_by=actor, updated_by=actor)

        obj = ser.save(**save_kwargs)
        out = TaskCompletedSerializer(obj, context={"request": request})
        return response.Response(out.data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=False, methods=["get"], url_path=r"by-customer/(?P<customer_id>\d+)",
                       permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated])
    def by_customer(self, request, customer_id=None):
        qs = (TaskCompleted.active_objects
              .filter(visit__subscription__customer_id=customer_id)
              .select_related("visit", "plan_task")
              .order_by("id"))
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = TaskCompletedSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(ser.data)
        ser = TaskCompletedSerializer(qs, many=True, context={"request": request})
        return response.Response(ser.data, status=status.HTTP_200_OK)
