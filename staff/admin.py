# staff/admin.py
from django.contrib import admin
from .models import Technician

@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "phone", "active")
    list_filter = ("active",)
    search_fields = ("user__username", "user__email", "phone")
