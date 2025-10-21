# visits/views/assessments.py
import os
from django.db import transaction
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, decorators, response, status, filters

from ..models import Visit, Assessment
from ..serializers import AssessmentSerializer

DISABLE_AUTH = os.getenv("DISABLE_AUTH", "0") == "1"

def _actor_or_none(request):
    u = getattr(request, "user", None)
    return u if (u and getattr(u, "is_authenticated", False)) else None


class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.active_objects.select_related("visit").all().order_by("-created_at", "id")
    serializer_class = AssessmentSerializer
    permission_classes = [permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["visit", "rating"]
    search_fields = ["comment", "visit__notes"]
    ordering_fields = ["created_at", "rating", "id"]
    ordering = ["-created_at", "id"]

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
        return response.Response({"detail": "Assessment restored"}, status=status.HTTP_200_OK)

    @decorators.action(detail=False, methods=["get", "post"], url_path=r"by-visit/(?P<visit_id>\d+)",
                       permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated])
    def by_visit(self, request, visit_id=None):
        visit = get_object_or_404(Visit.objects, pk=visit_id)

        if request.method.lower() == "get":
            obj = getattr(visit, "assessment", None)
            if not obj or not obj.active:
                return response.Response(None, status=status.HTTP_200_OK)
            ser = AssessmentSerializer(obj, context={"request": request})
            return response.Response(ser.data, status=status.HTTP_200_OK)

        ser = AssessmentSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)

        actor = _actor_or_none(request)
        with transaction.atomic():
            try:
                obj = visit.assessment
                if not obj.active:
                    obj.active = True
                obj.rating = ser.validated_data.get("rating", obj.rating)
                obj.comment = ser.validated_data.get("comment", obj.comment)
                if actor:
                    obj.updated_by = actor
                obj.save()
            except Assessment.DoesNotExist:
                save_kwargs = {"visit": visit}
                if actor:
                    save_kwargs.update(created_by=actor, updated_by=actor)
                obj = Assessment.objects.create(**save_kwargs, **ser.validated_data)

        out = AssessmentSerializer(obj, context={"request": request})
        return response.Response(out.data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=False, methods=["get"], url_path=r"by-customer/(?P<customer_id>\d+)",
                       permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated])
    def by_customer(self, request, customer_id=None):
        qs = (Assessment.active_objects
              .filter(visit__subscription__customer_id=customer_id)
              .select_related("visit")
              .order_by("-created_at", "id"))
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = AssessmentSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(ser.data)
        ser = AssessmentSerializer(qs, many=True, context={"request": request})
        return response.Response(ser.data, status=status.HTTP_200_OK)
