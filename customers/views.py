import os
from django.db import transaction
from rest_framework import viewsets, permissions, decorators, response, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError

from .models import Customer, CustomerContact
from .serializers import CustomerSerializer, CustomerContactSerializer

DISABLE_AUTH = os.getenv("DISABLE_AUTH", "0") == "1"

def _actor_or_none(request):
    u = getattr(request, "user", None)
    return u if (u and getattr(u, "is_authenticated", False)) else None

# -------- Customers (igual que ya tenías) --------
class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.active_objects.all().order_by("name", "id")
    serializer_class = CustomerSerializer
    permission_classes = [permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["active", "identification"]
    search_fields = ["name", "email", "phone", "location", "direction", "identification"]
    ordering_fields = ["name", "id", "created_at", "updated_at"]
    ordering = ["name"]

    def perform_create(self, serializer):
        actor = _actor_or_none(self.request)
        serializer.save(created_by=actor, updated_by=actor)

    def perform_update(self, serializer):
        actor = _actor_or_none(self.request)
        serializer.save(updated_by=actor)

    def perform_destroy(self, instance):
        instance.delete()

    @decorators.action(detail=True, methods=["post"], permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated])
    def restore(self, request, pk=None):
        obj = self.get_object()
        obj.active = True
        obj.save(update_fields=["active"])
        return response.Response({"detail": "Customer restored"}, status=status.HTTP_200_OK)

# -------- CustomerContacts (no anidado) --------
class CustomerContactViewSet(viewsets.ModelViewSet):
    queryset = CustomerContact.active_objects.all().order_by("name", "id")
    serializer_class = CustomerContactSerializer
    permission_classes = [permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["active", "is_main", "customer", "email"]
    search_fields = ["name", "email", "phone"]
    ordering_fields = ["id", "name", "email", "is_main", "created_at", "updated_at"]
    ordering = ["name"]

    def get_queryset(self):
        qs = super().get_queryset()
        # Permite filtrar por ?customer=<id> y ?only_main=1
        customer_id = self.request.query_params.get("customer")
        only_main = self.request.query_params.get("only_main")
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        if only_main in ("1", "true", "True"):
            qs = qs.filter(is_main=True)
        return qs

    def perform_create(self, serializer):
        actor = _actor_or_none(self.request)

        # Fuente del customer: body o ?customer=<id>
        body_customer = self.request.data.get("customer")
        query_customer = self.request.query_params.get("customer")
        customer_id = body_customer if body_customer not in (None, "", 0, "0") else query_customer

        if not customer_id and "customer" not in serializer.validated_data:
            raise ValidationError({"customer": "Este campo es requerido (puedes enviarlo en el body o como ?customer=<id>)."})
        # Si no vino en validated_data, forzamos por kwargs
        save_kwargs = {}
        if "customer" not in serializer.validated_data and customer_id:
            save_kwargs["customer_id"] = customer_id

        # Unicidad de principal por cliente si se crea como is_main=True
        is_main = bool(serializer.validated_data.get("is_main", False))
        with transaction.atomic():
            if is_main:
                cid = save_kwargs.get("customer_id") or serializer.validated_data["customer"].id
                CustomerContact.objects.filter(customer_id=cid, is_main=True).update(is_main=False)
            if actor:
                save_kwargs.update(created_by=actor, updated_by=actor)
            serializer.save(**save_kwargs)

    def perform_update(self, serializer):
        actor = _actor_or_none(self.request)
        # Si cambia a principal, desmarcamos otros del mismo cliente
        instance = self.get_object()
        will_be_main = serializer.validated_data.get("is_main", instance.is_main)
        with transaction.atomic():
            if will_be_main:
                CustomerContact.objects.filter(customer=instance.customer, is_main=True).exclude(pk=instance.pk).update(is_main=False)
            if actor:
                serializer.save(updated_by=actor)
            else:
                serializer.save()

    def perform_destroy(self, instance):
        instance.delete()

    @decorators.action(detail=True, methods=["post"], permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated])
    def restore(self, request, pk=None):
        obj = self.get_object()
        obj.active = True
        obj.save(update_fields=["active"])
        return response.Response({"detail": "Contact restored"}, status=status.HTTP_200_OK)

    @decorators.action(detail=True, methods=["post"], permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated])
    @transaction.atomic
    def set_main(self, request, pk=None):
        obj = self.get_object()
        CustomerContact.objects.filter(customer=obj.customer, is_main=True).exclude(pk=obj.pk).update(is_main=False)
        if not obj.is_main:
            obj.is_main = True
            obj.save(update_fields=["is_main"])
        ser = CustomerContactSerializer(obj, context={"request": request})
        return response.Response(ser.data, status=status.HTTP_200_OK)
