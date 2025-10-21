# users/views.py
import os
from rest_framework import viewsets, permissions, decorators, response, status
from django.db.models import Q
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import UserSerializer, UserCreateSerializer, EmailTokenObtainPairSerializer

class IsAdmin(permissions.IsAdminUser):
    """Permite solo a staff/superuser."""
    pass

DISABLE_AUTH = os.getenv("DISABLE_AUTH", "0") == "1"

def _actor_or_none(request):
    u = getattr(request, "user", None)
    return u if (u and getattr(u, "is_authenticated", False)) else None

class UserViewSet(viewsets.ModelViewSet):
    # Solo usuarios activos por defecto (si usas BaseModel.active + ActiveManager)
    queryset = User.active_objects.all().order_by("id")

    # —— Permisos por acción ——
    def get_permissions(self):
        if DISABLE_AUTH:
            # Modo pruebas: todo abierto
            return [permissions.AllowAny()]

        # Producción (por defecto):
        if self.action in ["list", "create", "destroy", "restore"]:
            return [IsAdmin()]
        # retrieve / update / partial_update / me
        return [permissions.IsAuthenticated()]

    # —— Alcance de consulta ——
    def get_queryset(self):
        qs = super().get_queryset()
        if DISABLE_AUTH:
            return qs
        user = self.request.user
        if user.is_staff:
            return qs
        # usuario normal solo se ve a sí mismo
        return qs.filter(id=user.id)

    # —— Serializers ——
    def get_serializer_class(self):
        return UserCreateSerializer if self.action == "create" else UserSerializer

    # —— Trazabilidad ——
    def perform_create(self, serializer):
        actor = _actor_or_none(self.request)
        if actor:
            serializer.save(created_by=actor, updated_by=actor)
        else:
            serializer.save()

    def perform_update(self, serializer):
        actor = _actor_or_none(self.request)
        if actor:
            serializer.save(updated_by=actor)
        else:
            serializer.save()

    # —— Soft delete: desactiva login también ——
    def perform_destroy(self, instance):
        instance.active = False
        if hasattr(instance, "is_active"):
            instance.is_active = False
            instance.save(update_fields=["active", "is_active"])
        else:
            instance.save(update_fields=["active"])

    # Reactivar (solo admin)
    @decorators.action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def restore(self, request, pk=None):
        obj = self.get_object()
        obj.active = True
        if hasattr(obj, "is_active"):
            obj.is_active = True
            obj.save(update_fields=["active", "is_active"])
        else:
            obj.save(update_fields=["active"])
        return response.Response({"detail": "User restored"}, status=status.HTTP_200_OK)

    # /api/users/me/
    @decorators.action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def me(self, request):
        user = request.user if (request.user and request.user.is_authenticated) else None
        if not DISABLE_AUTH and not user:
            return response.Response({"detail": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        ser = UserSerializer(user or User(), context={"request": request})
        return response.Response(ser.data)

class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer