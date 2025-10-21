from rest_framework.routers import DefaultRouter
from visits.views import (
    VisitViewSet,
    AssessmentViewSet,
    EvidenceViewSet,
    TaskCompletedViewSet,
    MaterialUsedViewSet,
)

router = DefaultRouter()
router.register(r"visit", VisitViewSet, basename="visit")
router.register(r"assessment", AssessmentViewSet, basename="assessment")
router.register(r"evidence", EvidenceViewSet, basename="evidence")
router.register(r"task-completed", TaskCompletedViewSet, basename="task-completed")
router.register(r"material-used", MaterialUsedViewSet, basename="material-used")

urlpatterns = router.urls
