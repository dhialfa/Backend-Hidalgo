from rest_framework import serializers
from .models import Plan, PlanTask, PlanSubscription

class PlanTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanTask
        fields = ["id", "plan", "name", "description", "order"]

class PlanSerializer(serializers.ModelSerializer):
    tasks = PlanTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Plan
        fields = ["id", "name", "description", "price", "active", "tasks"]

class PlanSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanSubscription
        fields = ["id", "customer", "plan", "start_date", "status", "notes"]
