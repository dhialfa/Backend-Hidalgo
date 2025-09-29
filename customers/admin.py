from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "identification", "email", "phone", "active")
    search_fields = ("name", "identification", "email", "phone")
    list_filter = ("active",)
