from rest_framework import serializers
from .models import PlanSubscription

class PlanSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanSubscription
        fields = ["id", "customer", "plan", "start_date", "end_date", "status", "notes"]

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if end and start and end < start:
            raise serializers.ValidationError({"end_date": "end_date cannot be before start_date."})
        return attrs
