# plans/views.py
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Plan, PlanTask
from .serializers import PlanSerializer, PlanTaskSerializer


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all().order_by("name")
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]   # ajusta en producción
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["periodicity", "active"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "price"]


class PlanTaskViewSet(viewsets.ModelViewSet):
    queryset = PlanTask.objects.select_related("plan").all().order_by("plan_id", "order")
    serializer_class = PlanTaskSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["plan"]
    search_fields = ["name", "description"]
    ordering_fields = ["order", "name"]
