from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from .views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    # OpenAPI / Swagger
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("", HealthCheckView.as_view(), name="health-check"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    # API
    path("api/auth/", include("jwt_auth.urls")),
    path("api/", include("users.urls")),
    path("api/", include("comments.urls")),
    path("api/", include("departments.urls")),
    path("api/", include("clocks.urls")),
    path("api/", include("plannings.urls")),
    path("api/", include("permissions.urls")),
]
