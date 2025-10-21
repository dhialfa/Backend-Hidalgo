from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","username","first_name","last_name","email","is_staff","is_active","is_superuser","last_login","date_joined","phone"]
        read_only_fields = ["id","is_superuser","last_login","date_joined"]

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ["username","password","first_name","last_name","email","phone","is_staff","is_active"]
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD  # <-- le decimos que el campo sea 'email'

    def validate(self, attrs):
        # obtenemos el email en lugar del username
        credentials = {
            'email': attrs.get('email'),
            'password': attrs.get('password')
        }

        # verificamos que no estén vacíos
        if not credentials['email'] or not credentials['password']:
            raise serializers.ValidationError("Debe incluir 'email' y 'password'.")

        # autenticamos con el backend de Django
        from django.contrib.auth import authenticate
        user = authenticate(**credentials)

        if user is None or not user.is_active:
            raise serializers.ValidationError("Credenciales inválidas.")

        refresh = self.get_token(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    # redefinimos los campos esperados
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['username'] = user.username
        return token