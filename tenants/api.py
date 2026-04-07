from rest_framework import permissions, viewsets
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet

from .filters import (
    ActivityLogFilter,
    AuditLogFilter,
    BillingHistoryFilter,
    MembershipFilter,
    OrganizationFilter,
    UsageMetricFilter,
    UserFilter,
)
from .models import (
    ActivityLog,
    AuditLog,
    BillingHistory,
    Membership,
    Organization,
    UsageMetric,
    User,
)
from .serializers import (
    ActivityLogSerializer,
    AuditLogSerializer,
    BillingHistorySerializer,
    MembershipSerializer,
    OrganizationSerializer,
    UsageMetricSerializer,
    UserSerializer,
)


class TenantScopedMixin:
    """Mixin that scopes querysets to the current tenant organization."""

    def get_organization(self):
        return getattr(self.request, "organization", None)


class OrganizationViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    filterset_class = OrganizationFilter
    search_fields = ["name", "slug"]
    ordering_fields = ["name", "created_at", "plan"]

    def get_queryset(self):
        org = self.get_organization()
        if org:
            return Organization.objects.filter(id=org.id)
        return Organization.objects.none()


class UserViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    serializer_class = UserSerializer
    filterset_class = UserFilter
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["username", "date_joined", "role"]

    def get_queryset(self):
        org = self.get_organization()
        if org:
            return User.objects.filter(
                memberships__organization=org,
                memberships__is_active=True,
            ).distinct()
        return User.objects.none()


class UsageMetricViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    serializer_class = UsageMetricSerializer
    filterset_class = UsageMetricFilter
    search_fields = ["metric_name"]
    ordering_fields = ["metric_name", "value", "period_start"]

    def get_queryset(self):
        org = self.get_organization()
        if org:
            return UsageMetric.objects.filter(organization=org)
        return UsageMetric.objects.none()


class MembershipViewSet(TenantScopedMixin, viewsets.ModelViewSet):
    serializer_class = MembershipSerializer
    filterset_class = MembershipFilter
    search_fields = ["user__username", "user__email", "user__first_name", "user__last_name"]
    ordering_fields = ["role", "joined_at", "user__username"]

    def get_queryset(self):
        org = self.get_organization()
        if org:
            return Membership.objects.filter(
                organization=org
            ).select_related("user", "organization")
        return Membership.objects.none()


class ActivityLogViewSet(TenantScopedMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """Read-only viewset for activity logs, scoped to current tenant."""
    serializer_class = ActivityLogSerializer
    filterset_class = ActivityLogFilter
    search_fields = ["action", "detail", "user__username"]
    ordering_fields = ["created_at", "action"]

    def get_queryset(self):
        org = self.get_organization()
        if org:
            return ActivityLog.objects.filter(
                organization=org
            ).select_related("user")
        return ActivityLog.objects.none()


class AuditLogViewSet(TenantScopedMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """Read-only viewset for audit logs, scoped to current tenant."""
    serializer_class = AuditLogSerializer
    filterset_class = AuditLogFilter
    search_fields = ["action", "target_model", "user__username"]
    ordering_fields = ["created_at", "action", "target_model"]

    def get_queryset(self):
        org = self.get_organization()
        if org:
            return AuditLog.objects.filter(
                organization=org
            ).select_related("user")
        return AuditLog.objects.none()


class BillingHistoryViewSet(TenantScopedMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """Read-only viewset for billing history, scoped to current tenant."""
    serializer_class = BillingHistorySerializer
    filterset_class = BillingHistoryFilter
    search_fields = ["description", "invoice_number"]
    ordering_fields = ["invoice_date", "amount", "status"]

    def get_queryset(self):
        org = self.get_organization()
        if org:
            return BillingHistory.objects.filter(organization=org)
        return BillingHistory.objects.none()
