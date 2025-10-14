from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Visit, Assessment, Evidence, TaskCompleted, MaterialUsed
from .serializers import (
    VisitSerializer, AssessmentSerializer, EvidenceSerializer,
    TaskCompletedSerializer, MaterialUsedSerializer
)

class BaseAuthViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

class VisitViewSet(BaseAuthViewSet):
    queryset = Visit.objects.select_related("subscription","user").all()
    serializer_class = VisitSerializer
    filterset_fields = ["subscription", "user", "status", "start", "end"]
    search_fields = ["site_address", "notes", "cancel_reason"]
    ordering_fields = ["start", "end", "updated_at"]

class AssessmentViewSet(BaseAuthViewSet):
    queryset = Assessment.objects.select_related("visit").all()
    serializer_class = AssessmentSerializer
    filterset_fields = ["visit", "rating"]
    ordering_fields = ["created_at"]

class EvidenceViewSet(BaseAuthViewSet):
    queryset = Evidence.objects.select_related("visit").all()
    serializer_class = EvidenceSerializer
    filterset_fields = ["visit"]
    ordering_fields = ["subido_en"]

class TaskCompletedViewSet(BaseAuthViewSet):
    queryset = TaskCompleted.objects.select_related("visit", "plan_task").all()
    serializer_class = TaskCompletedSerializer
    filterset_fields = ["visit", "plan_task", "completada"]
    ordering_fields = ["id", "hours"]

class MaterialUsedViewSet(BaseAuthViewSet):
    queryset = MaterialUsed.objects.select_related("visit").all()
    serializer_class = MaterialUsedSerializer
    filterset_fields = ["visit"]
    ordering_fields = ["unit_cost"]
