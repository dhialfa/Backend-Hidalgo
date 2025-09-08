from django.contrib.auth import get_user_model
from rest_framework import viewsets, status, permissions,filters
from rest_framework.decorators import action
from rest_framework.response import Response
##from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import AllowAny

from rest_framework import viewsets, permissions
from .serializers import UserSerializer

Usuario = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all().order_by("id")
    serializer_class = UserSerializer
    # Solo durante desarrollo; en producción usa permisos más estrictos
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        include_inactive = self.request.query_params.get("include_inactive")
        if include_inactive in ("1", "true", "True"):
            return qs
        return qs.filter(is_active=True)

    def destroy(self, request, *args, **kwargs):
        """Borrado lógico: is_active=False"""
        instance = self.get_object()
        if not instance.is_active:
            # ya estaba inactivo
            return Response(status=status.HTTP_204_NO_CONTENT)
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["patch"], url_path="restore")
    def restore(self, request, pk=None):
        """Restaurar (is_active=True)"""
        user = self.get_object()
        if user.is_active:
            return Response({"detail": "El usuario ya está activo."}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = True
        user.save(update_fields=["is_active"])
        return Response(self.get_serializer(user).data, status=status.HTTP_200_OK)
