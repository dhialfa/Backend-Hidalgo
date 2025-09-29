from rest_framework.routers import DefaultRouter
from .views import (
    VisitViewSet, AssessmentViewSet, EvidenceViewSet,
    TaskCompletedViewSet, MaterialUsedViewSet
)

router = DefaultRouter()
router.register(r"visits", VisitViewSet, basename="visits")
router.register(r"assessments", AssessmentViewSet, basename="assessments")
router.register(r"evidences", EvidenceViewSet, basename="evidences")
router.register(r"tasks-completed", TaskCompletedViewSet, basename="tasks-completed")
router.register(r"materials-used", MaterialUsedViewSet, basename="materials-used")

urlpatterns = router.urls
