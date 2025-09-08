# plans/serializers.py
from rest_framework import serializers
from .models import Plan, PlanTask


class PlanTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanTask
        fields = ["id", "plan", "name", "description", "order"]


class PlanSerializer(serializers.ModelSerializer):
    # incluir las tareas del plan en lectura
    tasks = PlanTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Plan
        fields = ["id", "name", "description", "periodicity", "price", "active", "tasks"]
