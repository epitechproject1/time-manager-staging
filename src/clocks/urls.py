from rest_framework.routers import DefaultRouter

from .views import ClockViewSet

router = DefaultRouter()
router.register("clocks", ClockViewSet, basename="clocks")

urlpatterns = router.urls
