from django.contrib import admin
from django.urls import path, re_path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="API Sistema de Visitas",
        default_version="v1",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # APIs (no importes ViewSets aquí)
    path("backend/accounts/", include("accounts.urls")),
    path("backend/customers/", include("customers.urls")),
    path("backend/staff/", include("staff.urls")),
    path("backend/plans/", include("plans.urls")),

    # Swagger / ReDoc
    re_path(r"^backend/swagger(?P<format>\.json|\.yaml)$",
            schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("backend/swagger/",
         schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("backend/redoc/",
         schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
