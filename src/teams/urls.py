from rest_framework.routers import DefaultRouter

from .views import TeamsViewSet

router = DefaultRouter()
# router.register("teams", TeamsViewSet)
router.register("", TeamsViewSet, basename="teams")


urlpatterns = router.urls
