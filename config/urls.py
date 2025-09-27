from django.contrib import admin
from django.urls import path, re_path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

schema_view = get_schema_view(
    openapi.Info(title="Backend Hidalgo API", default_version="v1"),
    public=True,
    permission_classes=[AllowAny],
)

urlpatterns = [
    path("api/auth/", include("rest_framework.urls")),
    path("admin/", admin.site.urls),

    # API de usuarios
    path("api/", include("users.urls")),

    # JWT
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Swagger/ReDoc
    re_path(r"^backend/swagger(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("backend/swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("backend/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
