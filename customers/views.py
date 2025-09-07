
# customers/views.py
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction

from .models import Cliente, ContactoCliente
from .serializers import ClienteSerializer, ContactoClienteSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all().order_by("id")
    serializer_class = ClienteSerializer
    permission_classes = [permissions.AllowAny]  # ajusta a tu esquema de auth

    # Filtros / búsqueda / ordenación
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["activo", "identificacion"]
    search_fields = ["nombre_legal", "identificacion", "correo"]
    ordering_fields = ["id", "nombre_legal", "identificacion", "activo"]


class ContactoClienteViewSet(viewsets.ModelViewSet):
    queryset = ContactoCliente.objects.select_related("cliente").all().order_by("id")
    serializer_class = ContactoClienteSerializer
    permission_classes = [permissions.AllowAny]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["cliente", "es_principal", "correo"]
    search_fields = ["nombre", "correo", "telefono", "cliente__nombre_legal"]
    ordering_fields = ["id", "cliente", "es_principal"]

    @action(detail=True, methods=["post"], url_path="hacer-principal")
    def hacer_principal(self, request, pk=None):
        """
        Marca este contacto como principal y desmarca los demás del mismo cliente.
        """
        contacto = self.get_object()
        with transaction.atomic():
            contacto.es_principal = True
            contacto.save(update_fields=["es_principal"])
            ContactoCliente.objects.filter(
                cliente=contacto.cliente
            ).exclude(pk=contacto.pk).update(es_principal=False)
        return Response({"status": "ok", "contacto_principal_id": contacto.id})
