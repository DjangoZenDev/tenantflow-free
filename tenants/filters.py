import django_filters

from .models import (
    ActivityLog,
    AuditLog,
    BillingHistory,
    Membership,
    Organization,
    UsageMetric,
    User,
)


class OrganizationFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    plan = django_filters.ChoiceFilter(choices=Organization.PLAN_CHOICES)
    is_active = django_filters.BooleanFilter()
    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = Organization
        fields = ["name", "plan", "is_active"]


class UserFilter(django_filters.FilterSet):
    role = django_filters.ChoiceFilter(choices=User.ROLE_CHOICES)
    email = django_filters.CharFilter(lookup_expr="icontains")
    is_active = django_filters.BooleanFilter()
    joined_after = django_filters.DateTimeFilter(
        field_name="date_joined", lookup_expr="gte"
    )
    joined_before = django_filters.DateTimeFilter(
        field_name="date_joined", lookup_expr="lte"
    )

    class Meta:
        model = User
        fields = ["role", "email", "is_active"]


class UsageMetricFilter(django_filters.FilterSet):
    metric_name = django_filters.CharFilter(lookup_expr="icontains")
    min_value = django_filters.NumberFilter(field_name="value", lookup_expr="gte")
    max_value = django_filters.NumberFilter(field_name="value", lookup_expr="lte")
    period_start_after = django_filters.DateTimeFilter(
        field_name="period_start", lookup_expr="gte"
    )
    period_start_before = django_filters.DateTimeFilter(
        field_name="period_start", lookup_expr="lte"
    )

    class Meta:
        model = UsageMetric
        fields = ["metric_name"]


class MembershipFilter(django_filters.FilterSet):
    role = django_filters.ChoiceFilter(choices=User.ROLE_CHOICES)
    is_active = django_filters.BooleanFilter()
    user = django_filters.NumberFilter(field_name="user__id")
    username = django_filters.CharFilter(
        field_name="user__username", lookup_expr="icontains"
    )
    joined_after = django_filters.DateTimeFilter(
        field_name="joined_at", lookup_expr="gte"
    )
    joined_before = django_filters.DateTimeFilter(
        field_name="joined_at", lookup_expr="lte"
    )

    class Meta:
        model = Membership
        fields = ["role", "is_active", "user"]


class ActivityLogFilter(django_filters.FilterSet):
    action = django_filters.CharFilter(lookup_expr="icontains")
    user = django_filters.NumberFilter(field_name="user__id")
    target_type = django_filters.CharFilter(lookup_expr="iexact")
    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = ActivityLog
        fields = ["action", "user", "target_type"]


class AuditLogFilter(django_filters.FilterSet):
    action = django_filters.ChoiceFilter(choices=AuditLog.ACTION_CHOICES)
    target_model = django_filters.CharFilter(lookup_expr="iexact")
    user = django_filters.NumberFilter(field_name="user__id")
    created_after = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_before = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = AuditLog
        fields = ["action", "target_model", "user"]


class BillingHistoryFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=BillingHistory.STATUS_CHOICES)
    min_amount = django_filters.NumberFilter(field_name="amount", lookup_expr="gte")
    max_amount = django_filters.NumberFilter(field_name="amount", lookup_expr="lte")
    invoice_after = django_filters.DateFilter(
        field_name="invoice_date", lookup_expr="gte"
    )
    invoice_before = django_filters.DateFilter(
        field_name="invoice_date", lookup_expr="lte"
    )

    class Meta:
        model = BillingHistory
        fields = ["status"]
