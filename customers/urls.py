from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, CustomerContactViewSet

router = DefaultRouter()
router.register(r"customers", CustomerViewSet, basename="customer")
router.register(r"customer-contact", CustomerContactViewSet, basename="customer-contact")


urlpatterns = [
    path("", include(router.urls)),
]
