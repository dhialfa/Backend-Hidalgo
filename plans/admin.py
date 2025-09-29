from django.contrib import admin
from .models import Plan, PlanTask, PlanSubscription

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "active")
    search_fields = ("name",)
    list_filter = ("active",)

@admin.register(PlanTask)
class PlanTaskAdmin(admin.ModelAdmin):
    list_display = ("plan", "order", "name")
    list_filter = ("plan",)
    search_fields = ("name",)
    ordering = ("plan", "order")

@admin.register(PlanSubscription)
class PlanSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("customer", "plan", "start_date", "status")
    list_filter = ("status", "plan")
    search_fields = ("customer__name", "plan__name")
