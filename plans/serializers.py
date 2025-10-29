from rest_framework import serializers
from .models import Plan, PlanTask, PlanSubscription
# Si necesitas Customer info específica en otro serializer, importa:
# from customers.models import Customer


# ---- Tasks embebidas (solo lectura) ----
class PlanTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanTask
        fields = ["id", "name", "description"] 

class PlanSerializer(serializers.ModelSerializer):

    tasks = PlanTaskSerializer(many=True, read_only=True)  # o source="plantask_set"
    class Meta:
        model = Plan
        fields = ["id", "name", "description", "price", "active", "tasks"]


class PlanSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = PlanSubscription
        fields = ["id", "customer", "plan", "start_date", "status", "notes"]
        extra_kwargs = {
            "start_date": {"required": False},
            "notes": {"required": False},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")

        # SOLO en GET devolvemos detalles anidados
        if request and request.method == "GET":
            data["plan_detail"] = PlanSerializer(instance.plan, context=self.context).data
            c = instance.customer
            data["customer_info"] = {
                "id": c.id,
                "name": getattr(c, "name", None),
                "identification": getattr(c, "identification", None),
                "email": getattr(c, "email", None),
                "phone": getattr(c, "phone", None),
            } if c else None

        return data
