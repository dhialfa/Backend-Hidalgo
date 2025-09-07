# customers/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClienteViewSet, ContactoClienteViewSet

app_name = "customers"

router = DefaultRouter()
router.register(r"clientes", ClienteViewSet, basename="cliente")
router.register(r"contactos", ContactoClienteViewSet, basename="contacto")

urlpatterns = [
    path("", include(router.urls)),
]
