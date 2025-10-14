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
