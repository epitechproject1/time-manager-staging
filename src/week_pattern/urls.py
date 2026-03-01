from rest_framework.routers import DefaultRouter

from .views import WeekPatternViewSet

router = DefaultRouter()
# router.register("teams", TeamsViewSet)
router.register("week-pattern", WeekPatternViewSet, basename="week-pattern")


urlpatterns = router.urls
