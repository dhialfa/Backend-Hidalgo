from django.contrib.auth import get_user_model
from rest_framework import serializers

Usuario = get_user_model()

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Usuario
        # Campos de AbstractUser + extras (rol, telefono)
        fields = [
            "id", "username", "password", "first_name", "last_name", "email",
            "rol", "telefono",
            "is_active", "is_staff", "is_superuser",
            "last_login", "date_joined",
        ]
        read_only_fields = ["id", "last_login", "date_joined", "is_superuser"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = Usuario(**validated_data)
        if password:
            user.set_password(password)
        else:
            # Generar un password unusable si no se provee
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password is not None and password != "":
            instance.set_password(password)
        instance.save()
        return instance
