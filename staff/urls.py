from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TechnicianViewSet

app_name = "staff"

router = DefaultRouter()
router.register(r"technicians", TechnicianViewSet, basename="technician")

urlpatterns = [
    path("", include(router.urls)),
]
