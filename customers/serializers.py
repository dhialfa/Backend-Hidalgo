# customers/serializers.py
from django.db import transaction
from rest_framework import serializers
from .models import Cliente, ContactoCliente


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = [
            "id",
            "nombre_legal",
            "identificacion",
            "correo",
            "telefono",
            "direccion",
            "ubicacion",
            "activo",
        ]


class ContactoClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactoCliente
        fields = [
            "id",
            "cliente",
            "nombre",
            "correo",
            "telefono",
            "es_principal",
        ]

    def create(self, validated_data):
        # Si se crea como principal, desmarcar los demás contactos del mismo cliente
        with transaction.atomic():
            contacto = super().create(validated_data)
            if contacto.es_principal:
                ContactoCliente.objects.filter(
                    cliente=contacto.cliente
                ).exclude(pk=contacto.pk).update(es_principal=False)
        return contacto

    def update(self, instance, validated_data):
        # Si se actualiza a principal, desmarcar los demás contactos del mismo cliente
        with transaction.atomic():
            contacto = super().update(instance, validated_data)
            if contacto.es_principal:
                ContactoCliente.objects.filter(
                    cliente=contacto.cliente
                ).exclude(pk=contacto.pk).update(es_principal=False)
        return contacto



