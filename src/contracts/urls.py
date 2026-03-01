from rest_framework.routers import DefaultRouter

from .views.contract import ContractViewSet
from .views.contract_type import ContractTypeViewSet

router = DefaultRouter()

# Routes des types de contrat
router.register("contract-types", ContractTypeViewSet, basename="contract-type")

# Routes des contrats
router.register("contracts", ContractViewSet, basename="contract")

urlpatterns = router.urls
