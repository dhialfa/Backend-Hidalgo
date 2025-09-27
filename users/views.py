from rest_framework import viewsets, permissions
from .models import User
from .serializers import UserSerializer, UserCreateSerializer

class IsAdmin(permissions.IsAdminUser):
    pass

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    permission_classes = [IsAdmin]
    def get_serializer_class(self):
        if self.action in ["create"]:
            return UserCreateSerializer
        return UserSerializer
