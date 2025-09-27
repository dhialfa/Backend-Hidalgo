from django.contrib import admin
from django.urls import path, re_path, include

# API de tu app
api_patterns = [
    

]

# ---- Swagger (drf-yasg) ----
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Backend Hidalgo API",
        default_version="v1",
        description="API generada a partir del ERD (customers, plans, visits, etc.)",
        contact=openapi.Contact(email="tu-correo@ejemplo.com"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],  # si quieres protegerla, cambia a IsAuthenticated
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Tu API
    path("api/", include(api_patterns)),

    # Swagger / ReDoc
    re_path(r"^swagger(?P<format>\.json|\.yaml)$",
            schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
