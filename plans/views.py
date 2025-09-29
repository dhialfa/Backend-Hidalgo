from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Plan, PlanTask, PlanSubscription
from .serializers import PlanSerializer, PlanTaskSerializer, PlanSubscriptionSerializer

class BaseAuthViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

class PlanViewSet(BaseAuthViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    filterset_fields = ["active"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "price"]

class PlanTaskViewSet(BaseAuthViewSet):
    queryset = PlanTask.objects.select_related("plan").all()
    serializer_class = PlanTaskSerializer
    filterset_fields = ["plan"]
    search_fields = ["name", "description"]
    ordering_fields = ["order"]

class PlanSubscriptionViewSet(BaseAuthViewSet):
    queryset = PlanSubscription.objects.select_related("plan", "customer").all()
    serializer_class = PlanSubscriptionSerializer
    filterset_fields = ["customer", "plan", "status", "start_date"]
    search_fields = ["notes"]
    ordering_fields = ["start_date"]
