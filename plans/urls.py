from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, PlanTaskViewSet, PlanSubscriptionViewSet

router = DefaultRouter()
router.register(r"plans", PlanViewSet, basename="plans")
router.register(r"plan-tasks", PlanTaskViewSet, basename="plan-tasks")
router.register(r"plan-subscriptions", PlanSubscriptionViewSet, basename="plan-subscriptions")

urlpatterns = router.urls
