from rest_framework import serializers
from .models import Technician


class TechnicianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Technician
        fields = ["id", "user", "phone", "active"]

    def validate_user(self, value):
        # Errores legibles si ya existe Technician para ese user
        existing = getattr(value, "technician", None)
        if self.instance is None and existing:
            raise serializers.ValidationError("This user is already linked to a technician.")
        if self.instance and value != self.instance.user and existing:
            raise serializers.ValidationError("This user is already linked to a technician.")
        return value
