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
    path("api/auth/", include("reset_password.urls")),
    path("api/", include("users.urls")),
    path("api/", include("departments.urls")),
    path("api/", include("permissions.urls")),
    path("api/teams/", include("teams.urls")),
    path("api/", include("contracts.urls")),
    path("api/", include("override.urls")),
    path("api/", include("shift.urls")),
    path("api/", include("time_slot_pattern.urls")),
    path("api/", include("assignment.urls")),
    path("api/", include("week_pattern.urls")),
    path("api/", include("clock_event.urls")),
    path("api/", include("clock_validation.urls")),
]
