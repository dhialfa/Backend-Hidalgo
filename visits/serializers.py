from rest_framework import serializers
from .models import Visit, Assessment, Evidence, TaskCompleted, MaterialUsed

class MaterialUsedSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialUsed
        fields = ["id", "visit", "description", "unit", "unit_cost"]

class TaskCompletedSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskCompleted
        fields = ["id", "visit", "plan_task", "name", "description", "hours", "completada"]

class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = ["id", "visit", "file", "description", "subido_en"]
        read_only_fields = ["subido_en"]

class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ["id", "visit", "rating", "comment", "created_at"]
        read_only_fields = ["created_at"]

class VisitSerializer(serializers.ModelSerializer):
    assessment = AssessmentSerializer(read_only=True)
    evidences = EvidenceSerializer(many=True, read_only=True)
    tasks_completed = TaskCompletedSerializer(many=True, read_only=True)
    materials_used = MaterialUsedSerializer(many=True, read_only=True)

    class Meta:
        model = Visit
        fields = [
            "id","subscription","user","start","end","status","site_address",
            "notes","cancel_reason","created_at","updated_at",
            "assessment","evidences","tasks_completed","materials_used",
        ]
        read_only_fields = ["created_at","updated_at"]

    def to_representation(self, instance):
            data = super().to_representation(instance)
            sub = instance.subscription

            if sub:
                c = sub.customer
                p = sub.plan
                data["subscription_info"] = {
                    "id": sub.id,
                    "status": sub.status,
                    "start_date": str(sub.start_date),
                    "customer": {
                        "id": c.id,
                        "name": getattr(c, "name", None),
                        "email": getattr(c, "email", None),
                        "phone": getattr(c, "phone", None),
                    } if c else None,
                    "plan": {
                        "id": p.id,
                        "name": getattr(p, "name", None),
                        "price": str(p.price),
                    } if p else None,
                }

            return data