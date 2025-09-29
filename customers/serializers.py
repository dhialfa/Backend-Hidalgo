from rest_framework import serializers
from .models import Customer, CustomerContact

class CustomerMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("id", "name", "identification")

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"

class CustomerContactSerializer(serializers.ModelSerializer):
    # write: pk del customer
    customer = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(), write_only=True, required=False
    )
    # read: objeto resumido
    customer_detail = CustomerMiniSerializer(source="customer", read_only=True)

    class Meta:
        model = CustomerContact
        fields = (
            "id", "customer", "customer_detail",
            "name", "email", "phone", "is_main",
            "active", "created_at", "updated_at", "created_by", "updated_by",
        )
        read_only_fields = ("active", "created_at", "updated_at", "created_by", "updated_by")
