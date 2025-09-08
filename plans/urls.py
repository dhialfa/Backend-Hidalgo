# plans/urls.py
from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, PlanTaskViewSet

router = DefaultRouter()
router.register(r"plans", PlanViewSet, basename="plans")
router.register(r"tasks", PlanTaskViewSet, basename="plan-tasks")

urlpatterns = router.urls
