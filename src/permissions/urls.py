from rest_framework.routers import DefaultRouter

from .views import PermissionViewSet

router = DefaultRouter()
router.register("permission", PermissionViewSet, basename="permission")

urlpatterns = router.urls
