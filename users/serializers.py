from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_active",
            "is_superuser",
            "last_login",
            "date_joined",
            "phone",
        ]
        read_only_fields = ["id", "is_superuser", "last_login", "date_joined"]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "phone",
            "is_staff",
            "is_active",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Login usando email + password.
    No dependemos de USERNAME_FIELD.
    """

    # Campo que esperamos en el body del login
    username_field = "email"

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError(
                "Debe incluir 'email' y 'password'."
            )

        # 1) Buscar usuario por email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        # 2) Verificar que esté activo
        if not user.is_active:
            raise AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        # 3) Verificar contraseña
        if not user.check_password(password):
            raise AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        # 4) Generar tokens
        refresh = self.get_token(user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        # 5) Agregar el usuario
        data["user"] = UserSerializer(user).data

        # 6) Actualizar last_login
        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, user)

        # Necesario para SimpleJWT
        self.user = user

        return data

    @classmethod
    def get_token(cls, user):
        """
        Opcional: agregar más datos al JWT.
        """
        token = super().get_token(user)
        token["email"] = user.email
        token["username"] = user.username
        token["is_staff"] = user.is_staff
        return token
