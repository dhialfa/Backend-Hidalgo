from rest_framework import serializers
from .models import Plan, PlanTask, PlanSubscription

class PlanTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanTask
        fields = ["id", "plan", "name", "description"]

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ["id", "name", "description", "price", "active"]

class PlanSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanSubscription
        fields = ["id", "customer", "plan", "start_date", "status", "notes"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        c = instance.customer
        # Ajusta a los campos reales de tu modelo Customer
        data["customer_info"] = {
            "id": c.id,
            "name": getattr(c, "name", None),
            "identification": getattr(c, "identification", None),
            "email": getattr(c, "email", None),
            "phone": getattr(c, "phone", None),
        } if c else None
        return data