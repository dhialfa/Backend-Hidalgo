from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Extra", {"fields": ("phone",)}),
    )
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "phone")
