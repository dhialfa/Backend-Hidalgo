# visits/views/__init__.py
from .visits import VisitViewSet
from .assessments import AssessmentViewSet
from .evidences import EvidenceViewSet
from .tasks_completed import TaskCompletedViewSet
from .materials_used import MaterialUsedViewSet

__all__ = [
    "VisitViewSet",
    "AssessmentViewSet",
    "EvidenceViewSet",
    "TaskCompletedViewSet",
    "MaterialUsedViewSet",
]
