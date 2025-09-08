from rest_framework.routers import DefaultRouter
from .views import PlanSubscriptionViewSet

router = DefaultRouter()
router.register(r"subscriptions", PlanSubscriptionViewSet, basename="plan-subscriptions")

urlpatterns = router.urls

    