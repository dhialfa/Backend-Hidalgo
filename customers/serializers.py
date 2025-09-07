from django.db import transaction
from rest_framework import serializers
from .models import Customer, CustomerContact


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "legal_name",
            "identification",
            "email",
            "phone",
            "address",
            "location",
            "active",
        ]


class CustomerContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerContact
        fields = [
            "id",
            "customer",
            "name",
            "email",
            "phone",
            "is_primary",
        ]

    def create(self, validated_data):
        # If created as primary, unset other contacts of the same customer
        with transaction.atomic():
            contact = super().create(validated_data)
            if contact.is_primary:
                CustomerContact.objects.filter(
                    customer=contact.customer
                ).exclude(pk=contact.pk).update(is_primary=False)
        return contact

    def update(self, instance, validated_data):
        # If updated to primary, unset other contacts of the same customer
        with transaction.atomic():
            contact = super().update(instance, validated_data)
            if contact.is_primary:
                CustomerContact.objects.filter(
                    customer=contact.customer
                ).exclude(pk=contact.pk).update(is_primary=False)
        return contact