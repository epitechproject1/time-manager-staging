from rest_framework.routers import DefaultRouter

from .views import TeamsViewSet

router = DefaultRouter()
router.register("", TeamsViewSet, basename="teams")


urlpatterns = router.urls
