# visits/validations.py
from rest_framework.exceptions import ValidationError

def validate_visit_dates(serializer, instance=None):
    """Valida que end >= start (si ambos existen)."""
    start = serializer.validated_data.get("start", getattr(instance, "start", None))
    end = serializer.validated_data.get("end", getattr(instance, "end", None))
    if end and start and end < start:
        raise ValidationError({"end": "La fecha/hora de fin no puede ser anterior al inicio."})

def ensure_active_user(serializer, instance=None):
    """
    Bloquea asignación de usuarios inactivos.
    En update, si no viene en el payload, usa el del instance.
    """
    user = serializer.validated_data.get("user", getattr(instance, "user", None))
    if user is None:
        return
    if not getattr(user, "is_active", True):
        raise ValidationError({"user": "El usuario asignado está inactivo y no puede usarse en visitas."})

def ensure_active_subscription(serializer=None, instance=None, subscription_override=None):
    """
    Bloquea uso de suscripciones inactivas.
    - create: en serializer.validated_data
    - update: cae al instance si no viene
    - by-subscription POST: usar subscription_override
    """
    sub = subscription_override
    if sub is None:
        sub = serializer.validated_data.get("subscription", getattr(instance, "subscription", None)) if (serializer or instance) else None
    if sub is None:
        return
    if not getattr(sub, "active", True):
        raise ValidationError({"subscription": "La suscripción seleccionada está inactiva y no puede usarse en visitas."})
