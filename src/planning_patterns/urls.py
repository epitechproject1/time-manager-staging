from rest_framework.routers import DefaultRouter

from planning_patterns.views import (
    PlanningTemplateViewSet,
    TimeSlotPatternViewSet,
    WeekPatternViewSet,
)

router = DefaultRouter()

# Semaines types
router.register("week-patterns", WeekPatternViewSet, basename="week-pattern")

# Créneaux horaires
router.register(
    "time-slot-patterns", TimeSlotPatternViewSet, basename="time-slot-pattern"
)

# Templates de planning
router.register(
    "planning-templates", PlanningTemplateViewSet, basename="planning-template"
)

urlpatterns = router.urls
