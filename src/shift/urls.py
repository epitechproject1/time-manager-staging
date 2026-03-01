from rest_framework.routers import DefaultRouter

from shift.views import ShiftViewSet

router = DefaultRouter()

# Exceptions
router.register("shifts", ShiftViewSet, basename="shifts")

urlpatterns = router.urls
