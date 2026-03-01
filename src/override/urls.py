from rest_framework.routers import DefaultRouter

from override.views import ShiftOverrideViewSet

router = DefaultRouter()
router.register("shift-overrides", ShiftOverrideViewSet, basename="shift-override")

urlpatterns = router.urls
