from rest_framework.routers import DefaultRouter

from time_slot_pattern.views import TimeSlotPatternViewSet

router = DefaultRouter()
# router.register("teams", TeamsViewSet)
router.register(
    "time-slot-patterns", TimeSlotPatternViewSet, basename="time-slot-pattern"
)


urlpatterns = router.urls
