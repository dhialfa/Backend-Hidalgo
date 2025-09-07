from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Customer, CustomerContact
from .serializers import CustomerSerializer, CustomerContactSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("id")
    serializer_class = CustomerSerializer
    permission_classes = [permissions.AllowAny]  # adjust to your auth

    # Filters / search / ordering
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["active", "identification"]
    search_fields = ["legal_name", "identification", "email"]
    ordering_fields = ["id", "legal_name", "identification", "active"]


class CustomerContactViewSet(viewsets.ModelViewSet):
    queryset = CustomerContact.objects.select_related("customer").all().order_by("id")
    serializer_class = CustomerContactSerializer
    permission_classes = [permissions.AllowAny]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["customer", "is_primary", "email"]
    search_fields = ["name", "email", "phone", "customer__legal_name"]
    ordering_fields = ["id", "customer", "is_primary"]

    @action(detail=True, methods=["post"], url_path="set-primary")
    def set_primary(self, request, pk=None):
        """
        Mark this contact as primary and unset other contacts of the same customer.
        """
        contact = self.get_object()
        with transaction.atomic():
            contact.is_primary = True
            contact.save(update_fields=["is_primary"])
            CustomerContact.objects.filter(
                customer=contact.customer
            ).exclude(pk=contact.pk).update(is_primary=False)
        return Response({"status": "ok", "primary_contact_id": contact.id})