# visits/views/evidences.py
import os
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, decorators, response, status, filters

from ..models import Visit, Evidence
from ..serializers import EvidenceSerializer

DISABLE_AUTH = os.getenv("DISABLE_AUTH", "0") == "1"


def _actor_or_none(request):
    u = getattr(request, "user", None)
    return u if (u and getattr(u, "is_authenticated", False)) else None


class EvidenceViewSet(viewsets.ModelViewSet):
    queryset = Evidence.active_objects.select_related("visit").all().order_by("-subido_en", "id")
    serializer_class = EvidenceSerializer
    permission_classes = [permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["visit"]
    search_fields = ["description", "visit__notes", "visit__site_address"]
    ordering_fields = ["subido_en", "id", "created_at", "updated_at"]
    ordering = ["-subido_en", "id"]

    def perform_create(self, serializer):
        actor = _actor_or_none(self.request)
        kwargs = {"created_by": actor, "updated_by": actor} if actor else {}
        serializer.save(**kwargs)

    def perform_update(self, serializer):
        actor = _actor_or_none(self.request)
        kwargs = {"updated_by": actor} if actor else {}
        serializer.save(**kwargs)

    def perform_destroy(self, instance):
        instance.delete()

    @decorators.action(detail=True, methods=["post"], permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated])
    def restore(self, request, pk=None):
        obj = self.get_object()
        obj.active = True
        obj.save(update_fields=["active"])
        return response.Response({"detail": "Evidence restored"}, status=status.HTTP_200_OK)

    # by-visit (GET lista / POST sube)
    @decorators.action(detail=False, methods=["get", "post"], url_path=r"by-visit/(?P<visit_id>\d+)",
                       permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated])
    def by_visit(self, request, visit_id=None):
        visit = get_object_or_404(Visit.objects, pk=visit_id)

        if request.method.lower() == "get":
            qs = Evidence.active_objects.filter(visit=visit).order_by("-subido_en", "id")
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
        if actor:
            save_kwargs.update(created_by=actor, updated_by=actor)

        obj = ser.save(**save_kwargs)
        out = EvidenceSerializer(obj, context={"request": request})
        return response.Response(out.data, status=status.HTTP_201_CREATED)

    # by-customer (GET lista)
    @decorators.action(detail=False, methods=["get"], url_path=r"by-customer/(?P<customer_id>\d+)",
                       permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated])
    def by_customer(self, request, customer_id=None):
        qs = (Evidence.active_objects
              .filter(visit__subscription__customer_id=customer_id)
              .select_related("visit")
              .order_by("-subido_en", "id"))
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = EvidenceSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(ser.data)
        ser = EvidenceSerializer(qs, many=True, context={"request": request})
        return response.Response(ser.data, status=status.HTTP_200_OK)
