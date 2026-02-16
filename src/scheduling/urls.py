from rest_framework.routers import DefaultRouter

from scheduling.views import (
    ScheduleAssignmentViewSet,
    ShiftOverrideViewSet,
    ShiftViewSet,
)

router = DefaultRouter()

# Affectations de planning
router.register("assignments", ScheduleAssignmentViewSet, basename="assignment")

# Occurrences réelles
router.register("shifts", ShiftViewSet, basename="shift")

# Exceptions
router.register("shift-overrides", ShiftOverrideViewSet, basename="shift-override")

urlpatterns = router.urls
