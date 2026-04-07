from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api import (
    ActivityLogViewSet,
    AuditLogViewSet,
    BillingHistoryViewSet,
    MembershipViewSet,
    OrganizationViewSet,
    UsageMetricViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register(r"organizations", OrganizationViewSet, basename="organization")
router.register(r"users", UserViewSet, basename="user")
router.register(r"usage-metrics", UsageMetricViewSet, basename="usagemetric")
router.register(r"memberships", MembershipViewSet, basename="membership")
router.register(r"activity-logs", ActivityLogViewSet, basename="activitylog")
router.register(r"audit-logs", AuditLogViewSet, basename="auditlog")
router.register(r"billing-history", BillingHistoryViewSet, basename="billinghistory")

urlpatterns = [
    path("", include(router.urls)),
]
