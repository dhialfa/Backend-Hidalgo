from django.contrib import admin
from .models import Visit, Assessment, Evidence, TaskCompleted, MaterialUsed

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("id","subscription","user","start","end","status")
    list_filter = ("status","subscription__plan")
    search_fields = ("notes","site_address","cancel_reason")
    date_hierarchy = "start"

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("visit","rating","created_at")
    list_filter = ("rating",)

@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("visit","file","subido_en")
    list_filter = ("visit",)

@admin.register(TaskCompleted)
class TaskCompletedAdmin(admin.ModelAdmin):
    list_display = ("visit","plan_task","name","hours","completada")
    list_filter = ("completada","plan_task__plan")
    search_fields = ("name","description")

@admin.register(MaterialUsed)
class MaterialUsedAdmin(admin.ModelAdmin):
    list_display = ("visit","description","unit","unit_cost")
    list_filter = ("visit",)
