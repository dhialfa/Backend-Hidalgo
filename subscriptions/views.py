# subscriptions/views.py
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import PlanSubscription
from .serializers import PlanSubscriptionSerializer

class PlanSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = PlanSubscription.objects.select_related("customer", "plan").all()
    serializer_class = PlanSubscriptionSerializer
    permission_classes = [permissions.AllowAny]  # Ajusta en producción

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["customer", "plan", "status", "start_date", "end_date"]
    search_fields = ["notes"]
    ordering_fields = ["start_date", "end_date", "id"]
    ordering = ["-start_date", "id"]
