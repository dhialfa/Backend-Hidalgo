import os
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, decorators, response, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from .models import Plan, PlanTask, PlanSubscription, Customer
from .serializers import PlanSerializer, PlanTaskSerializer, PlanSubscriptionSerializer

# ---------- Auth toggle ----------
DISABLE_AUTH = os.getenv("DISABLE_AUTH", "0") == "1"

def _actor_or_none(request):
    u = getattr(request, "user", None)
    return u if (u and getattr(u, "is_authenticated", False)) else None


# ==================== Plans ====================
class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.active_objects.all().order_by("name", "id")
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["active"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "price", "id", "created_at", "updated_at"]
    ordering = ["name"]

    def perform_create(self, serializer):
        actor = _actor_or_none(self.request)
        serializer.save(created_by=actor, updated_by=actor)

    def perform_update(self, serializer):
        actor = _actor_or_none(self.request)
        serializer.save(updated_by=actor)

    def perform_destroy(self, instance):
        instance.delete()

    @decorators.action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def restore(self, request, pk=None):
        obj = self.get_object()
        obj.active = True
        obj.save(update_fields=["active"])
        return response.Response({"detail": "Plan restored"}, status=status.HTTP_200_OK)


# ==================== PlanTasks ====================
class PlanTaskViewSet(viewsets.ModelViewSet):
    queryset = PlanTask.active_objects.select_related("plan").all().order_by("name", "id")
    serializer_class = PlanTaskSerializer
    permission_classes = [permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["active", "plan"]
    search_fields = ["name", "description", "plan__name"]
    ordering_fields = ["name", "id", "created_at", "updated_at"]
    ordering = ["name"]

    def get_queryset(self):
        qs = super().get_queryset()
        plan_id = self.request.query_params.get("plan")
        if plan_id:
            qs = qs.filter(plan_id=plan_id)
        return qs

    def perform_create(self, serializer):
        actor = _actor_or_none(self.request)
        body_plan = self.request.data.get("plan")
        query_plan = self.request.query_params.get("plan")
        plan_id = body_plan if body_plan not in (None, "", 0, "0") else query_plan

        if not plan_id and "plan" not in serializer.validated_data:
            raise ValidationError({"plan": "Este campo es requerido (envíalo en el body o como ?plan=<id>)."})
        save_kwargs = {}

        # 🚫 Bloquear creación si el plan está inactivo
        plan_in = serializer.validated_data.get("plan")
        if plan_in is not None:
            if not plan_in.active:
                raise ValidationError({"plan": "No se pueden crear tareas en un plan inactivo."})
        else:
            if plan_id:
                plan = get_object_or_404(Plan.objects, pk=plan_id)
                if not plan.active:
                    raise ValidationError({"plan": "No se pueden crear tareas en un plan inactivo."})
                save_kwargs["plan"] = plan

        if actor:
            save_kwargs.update(created_by=actor, updated_by=actor)
        serializer.save(**save_kwargs)

    def perform_update(self, serializer):
        actor = _actor_or_none(self.request)
        instance = self.get_object()

        # 🚫 Bloquear edición si el plan asociado (nuevo o actual) está inactivo
        target_plan = serializer.validated_data.get("plan") or getattr(instance, "plan", None)
        if target_plan is not None and not target_plan.active:
            raise ValidationError({"plan": "No se pueden modificar tareas asociadas a un plan inactivo."})

        if actor:
            serializer.save(updated_by=actor)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        instance.delete()

    @decorators.action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def restore(self, request, pk=None):
        obj = self.get_object()
        obj.active = True
        obj.save(update_fields=["active"])
        return response.Response({"detail": "Task restored"}, status=status.HTTP_200_OK)

    # -------- by-plan (GET lista / POST crea) --------
    @decorators.action(
        detail=False,
        methods=["get", "post"],
        url_path=r"by-plan/(?P<plan_id>\d+)",
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def by_plan(self, request, plan_id=None):
        """
        GET  /api/plan-task/by-plan/<plan_id>/
        POST /api/plan-task/by-plan/<plan_id>/
        """
        plan = get_object_or_404(Plan.objects, pk=plan_id)

        if request.method.lower() == "get":
            qs = PlanTask.active_objects.filter(plan=plan).order_by("name", "id")

            page = self.paginate_queryset(qs)
            if page is not None:
                ser = PlanTaskSerializer(page, many=True, context={"request": request})
                return self.get_paginated_response(ser.data)

            ser = PlanTaskSerializer(qs, many=True, context={"request": request})
            return response.Response(ser.data, status=status.HTTP_200_OK)

        # 🚫 POST: crear task para ESTE plan -> bloquear si está inactivo
        if not plan.active:
            raise ValidationError({"plan": "No se pueden crear tareas en un plan inactivo."})

        ser = PlanTaskSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)

        actor = _actor_or_none(request)
        save_kwargs = {"plan": plan}
        if actor:
            save_kwargs.update(created_by=actor, updated_by=actor)

        obj = ser.save(**save_kwargs)
        out = PlanTaskSerializer(obj, context={"request": request})
        return response.Response(out.data, status=status.HTTP_201_CREATED)


# ==================== PlanSubscriptions ====================
class PlanSubscriptionViewSet(viewsets.ModelViewSet):
    queryset = (
        PlanSubscription.active_objects
        .select_related("plan", "customer")
        .all()
        .order_by("-start_date", "id")
    )
    serializer_class = PlanSubscriptionSerializer
    permission_classes = [permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["active", "customer", "plan", "status", "start_date"]
    search_fields = ["notes", "plan__name", "customer__name", "customer__identification"]
    ordering_fields = ["start_date", "end_date", "id", "created_at", "updated_at"]
    ordering = ["-start_date", "id"]

    def get_queryset(self):
        qs = super().get_queryset()
        # Atajos útiles: ?customer=<id>&plan=<id>
        customer_id = self.request.query_params.get("customer")
        plan_id = self.request.query_params.get("plan")
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        if plan_id:
            qs = qs.filter(plan_id=plan_id)
        return qs

    def _assert_plan_and_tasks_active(self, plan: Plan):
        if not plan.active:
            raise ValidationError({"plan": "No se pueden crear o modificar suscripciones con un plan inactivo."})
        if PlanTask.objects.filter(plan=plan, active=False).exists():
           raise ValidationError({"plan": "No se pueden crear o modificar suscripciones: el plan tiene tareas inactivas."})


    def perform_create(self, serializer):
        actor = _actor_or_none(self.request)
        save_kwargs = {}
        if actor:
            save_kwargs.update(created_by=actor, updated_by=actor)

        # 🚫 Validar que el plan esté activo y sin tareas inactivas
        plan = serializer.validated_data.get("plan")
        if plan:
            self._assert_plan_and_tasks_active(plan)

        # Reglas existentes (mantener)
        status_in = serializer.validated_data.get("status")
        customer = serializer.validated_data.get("customer")
        if status_in in ("active", "ACTIVE", "Active") and customer:
            with transaction.atomic():
                PlanSubscription.objects.filter(customer=customer, status__iexact="active").update(status="inactive")
                serializer.save(**save_kwargs)
                return

        serializer.save(**save_kwargs)

    def perform_update(self, serializer):
        actor = _actor_or_none(self.request)
        instance = self.get_object()

        # 🚫 Validar plan (nuevo o actual) y tareas relacionadas
        plan = serializer.validated_data.get("plan") or getattr(instance, "plan", None)
        if plan:
            self._assert_plan_and_tasks_active(plan)

        if actor:
            serializer.save(updated_by=actor)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        instance.delete()

    @decorators.action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def restore(self, request, pk=None):
        obj = self.get_object()
        obj.active = True
        obj.save(update_fields=["active"])
        return response.Response({"detail": "Subscription restored"}, status=status.HTTP_200_OK)

    # -------- by-customer (GET lista / POST crea) --------
    @decorators.action(
        detail=False,
        methods=["get", "post"],
        url_path=r"by-customer/(?P<customer_id>\d+)",
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def by_customer(self, request, customer_id=None):
        """
        GET  /api/plan-subscription/by-customer/<customer_id>/?status=active
        POST /api/plan-subscription/by-customer/<customer_id>/   (en body enviar plan, fechas, etc. SIN 'customer')
        """
        customer = get_object_or_404(Customer.objects, pk=customer_id)

        if request.method.lower() == "get":
            status_q = request.query_params.get("status")
            qs = PlanSubscription.active_objects.filter(customer=customer).select_related("plan").order_by("-start_date", "id")
            if status_q:
                qs = qs.filter(status__iexact=status_q)

            page = self.paginate_queryset(qs)
            if page is not None:
                ser = PlanSubscriptionSerializer(page, many=True, context={"request": request})
                return self.get_paginated_response(ser.data)

            ser = PlanSubscriptionSerializer(qs, many=True, context={"request": request})
            return response.Response(ser.data, status=status.HTTP_200_OK)

        # POST: crear suscripción para ESTE customer (no enviar 'customer' en body)
        ser = PlanSubscriptionSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)

        # 🚫 Validar plan y sus tareas
        plan = ser.validated_data.get("plan")
        if not plan:
            raise ValidationError({"plan": "Este campo es requerido."})
        self._assert_plan_and_tasks_active(plan)

        actor = _actor_or_none(request)
        save_kwargs = {"customer": customer}
        if actor:
            save_kwargs.update(created_by=actor, updated_by=actor)

        status_in = ser.validated_data.get("status")
        with transaction.atomic():
            if status_in in ("active", "ACTIVE", "Active"):
                PlanSubscription.objects.filter(customer=customer, status__iexact="active").update(status="inactive")
            obj = ser.save(**save_kwargs)

        out = PlanSubscriptionSerializer(obj, context={"request": request})
        return response.Response(out.data, status=status.HTTP_201_CREATED)

    # -------- by-plan (GET lista / POST crea) --------
    @decorators.action(
        detail=False,
        methods=["get", "post"],
        url_path=r"by-plan/(?P<plan_id>\d+)",
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def by_plan(self, request, plan_id=None):
        """
        GET  /api/plan-subscription/by-plan/<plan_id>/?status=active
        POST /api/plan-subscription/by-plan/<plan_id>/   (en body enviar customer, fechas, etc. SIN 'plan')
        """
        plan = get_object_or_404(Plan.objects, pk=plan_id)

        if request.method.lower() == "get":
            status_q = request.query_params.get("status")
            qs = PlanSubscription.active_objects.filter(plan=plan).select_related("customer").order_by("-start_date", "id")
            if status_q:
                qs = qs.filter(status__iexact=status_q)

            page = self.paginate_queryset(qs)
            if page is not None:
                ser = PlanSubscriptionSerializer(page, many=True, context={"request": request})
                return self.get_paginated_response(ser.data)

            ser = PlanSubscriptionSerializer(qs, many=True, context={"request": request})
            return response.Response(ser.data, status=status.HTTP_200_OK)

        # 🚫 POST: crear suscripción para ESTE plan -> bloquear si plan inactivo o con tasks inactivas
        if not plan.active or PlanTask.objects.filter(plan=plan, active=False).exists():
            raise ValidationError({"plan": "No se pueden crear suscripciones: plan inactivo o con tareas inactivas."})

        ser = PlanSubscriptionSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)

        actor = _actor_or_none(request)
        save_kwargs = {"plan": plan}
        if actor:
            save_kwargs.update(created_by=actor, updated_by=actor)

        customer = ser.validated_data.get("customer")
        status_in = ser.validated_data.get("status")
        with transaction.atomic():
            if status_in in ("active", "ACTIVE", "Active") and customer:
                PlanSubscription.objects.filter(customer=customer, status__iexact="active").update(status="inactive")
            obj = ser.save(**save_kwargs)

        out = PlanSubscriptionSerializer(obj, context={"request": request})
        return response.Response(out.data, status=status.HTTP_201_CREATED)

    # -------- Acciones rápidas de estado (opcionales) --------
    @decorators.action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.AllowAny] if DISABLE_AUTH else [permissions.IsAuthenticated],
    )
    def cancel(self, request, pk=None):
        """Marcar suscripción como cancelada."""
        obj = self.get_object()
        obj.status = "cancelled"
        obj.save(update_fields=["status"])
        return response.Response({"detail": "Subscription cancelled"}, status=status.HTTP_200_OK)
