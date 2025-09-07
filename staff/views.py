from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Technician
from .serializers import TechnicianSerializer


class TechnicianViewSet(viewsets.ModelViewSet):
    queryset = Technician.objects.select_related("user").all().order_by("id")
    serializer_class = TechnicianSerializer
    permission_classes = [permissions.AllowAny]  # ajusta a tu auth

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["active", "user"]
    search_fields = ["phone", "user__username", "user__email", "user__first_name", "user__last_name"]
    ordering_fields = ["id", "user", "active"]
