# users/views.py
import os
from rest_framework import viewsets, permissions, decorators, response, status
from .models import User
from .serializers import UserSerializer, UserCreateSerializer, EmailTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class IsAdmin(permissions.IsAdminUser):
    pass

DISABLE_AUTH = os.getenv("DISABLE_AUTH", "0") == "1"

def _actor_or_none(request):
    u = getattr(request, "user", None)
    return u if (u and getattr(u, "is_authenticated", False)) else None

class UserViewSet(viewsets.ModelViewSet):
    queryset = (
        User.active_objects.all().order_by("id")
        if hasattr(User, "active_objects")
        else User.objects.all().order_by("id")
    )

    def get_permissions(self):
        if DISABLE_AUTH:
            return [permissions.AllowAny()]
        if self.action in ["list", "create", "destroy", "restore"]:
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        if DISABLE_AUTH:
            return qs
        user = self.request.user
        if getattr(user, "is_staff", False):
            return qs
        return qs.filter(id=user.id)

    def get_serializer_class(self):
        return UserCreateSerializer if self.action == "create" else UserSerializer

    def perform_create(self, serializer):
        actor = _actor_or_none(self.request)
        if actor and hasattr(User, "created_by"):
            serializer.save(created_by=actor, updated_by=actor)
        else:
            serializer.save()

    def perform_update(self, serializer):
        actor = _actor_or_none(self.request)
        if actor and hasattr(User, "updated_by"):
            serializer.save(updated_by=actor)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        if hasattr(instance, "active"):
            instance.active = False
        if hasattr(instance, "is_active"):
            instance.is_active = False
        instance.save()

    @decorators.action(detail=True, methods=["post"], permission_classes=[IsAdmin])
    def restore(self, request, pk=None):
        obj = self.get_object()
        if hasattr(obj, "active"):
            obj.active = True
        if hasattr(obj, "is_active"):
            obj.is_active = True
        obj.save()
        return response.Response({"detail": "User restored"}, status=status.HTTP_200_OK)

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