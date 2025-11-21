# analytics/views.py (o donde tengas tu DashboardOverviewView)
from datetime import date
from django.utils import timezone
from django.db.models import Count, Sum
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from customers.models import Customer
from plans.models import PlanSubscription
from visits.models import Visit


class DashboardOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # ---- Rango de fechas (mes actual por defecto) ----
        today = timezone.localdate()
        first_day = today.replace(day=1)

        from_str = request.query_params.get("from")
        to_str = request.query_params.get("to")

        if from_str:
            from_date = date.fromisoformat(from_str)
        else:
            from_date = first_day

        if to_str:
            to_date = date.fromisoformat(to_str)
        else:
            to_date = today

        # ---- Query base de visitas en el rango ----
        # OJO: aquí usamos start__date, no start_datetime
        visits_qs = Visit.objects.filter(
            start__date__gte=from_date,
            start__date__lte=to_date,
        )

        # Si quieres que los técnicos vean solo sus visitas:
        # if not request.user.is_staff:
        #     visits_qs = visits_qs.filter(user=request.user)

        # ---- Cards: totales simples ----
        total_customers = Customer.objects.count()
        active_customers = Customer.objects.filter(active=True).count()

        active_subscriptions = PlanSubscription.objects.filter(active=True).count()

        visits_planned_today = Visit.objects.filter(
            start__date=today,
            status="PENDIENTE",  # ajusta al valor real de tu choice
        ).count()

        visits_completed_today = Visit.objects.filter(
            end__date=today,
            status="COMPLETADA",  # ajusta al valor real de tu choice
        ).count()

        visits_completed_range = visits_qs.filter(status="COMPLETADA").count()

        revenue_qs = PlanSubscription.objects.filter(active=True).aggregate(
            total_revenue=Sum("plan__price")
        )
        estimated_monthly_revenue = revenue_qs["total_revenue"] or 0

        # ---- Gráfico: visitas por estado ----
        visits_by_status = list(
            visits_qs.values("status").annotate(count=Count("id")).order_by("status")
        )

        # ---- Gráfico: visitas por día (agrupado por fecha de start) ----
        visits_by_day_qs = (
            visits_qs.values("start__date")
            .annotate(count=Count("id"))
            .order_by("start__date")
        )
        visits_by_day = [
            {"date": row["start__date"], "count": row["count"]}
            for row in visits_by_day_qs
        ]

        data = {
            "range": {
                "from": from_date,
                "to": to_date,
            },
            "totals": {
                "total_customers": total_customers,
                "active_customers": active_customers,
                "active_subscriptions": active_subscriptions,
                "visits_planned_today": visits_planned_today,
                "visits_completed_today": visits_completed_today,
                "visits_completed_range": visits_completed_range,
                "estimated_monthly_revenue": estimated_monthly_revenue,
            },
            "charts": {
                "visits_by_status": visits_by_status,
                "visits_by_day": visits_by_day,
            },
        }

        return Response(data)
