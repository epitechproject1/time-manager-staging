from rest_framework.routers import DefaultRouter

from assignment.views import ScheduleAssignmentViewSet

router = DefaultRouter()
# router.register("teams", TeamsViewSet)
router.register("assignments", ScheduleAssignmentViewSet, basename="assignment")


urlpatterns = router.urls
