from rest_framework import serializers

from .models import (
    ActivityLog,
    AuditLog,
    BillingHistory,
    GlobalSetting,
    Membership,
    Organization,
    PlanFeature,
    UsageMetric,
    UsageSnapshot,
    User,
)


class OrganizationSerializer(serializers.ModelSerializer):
    member_count = serializers.ReadOnlyField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "plan",
            "is_active",
            "created_at",
            "member_count",
        ]
        read_only_fields = ["id", "created_at"]


class MembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_full_name = serializers.SerializerMethodField()
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    role_badge_color = serializers.ReadOnlyField()

    class Meta:
        model = Membership
        fields = [
            "id",
            "user",
            "organization",
            "role",
            "joined_at",
            "is_active",
            "username",
            "user_email",
            "user_full_name",
            "organization_name",
            "role_badge_color",
        ]
        read_only_fields = ["id", "joined_at"]

    def get_user_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username


class UserSerializer(serializers.ModelSerializer):
    initials = serializers.ReadOnlyField()
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    current_membership = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "initials",
            "organization_name",
            "date_joined",
            "is_active",
            "current_membership",
        ]
        read_only_fields = ["id", "date_joined", "username"]

    def get_current_membership(self, obj):
        if obj.organization:
            try:
                membership = Membership.objects.get(
                    user=obj, organization=obj.organization, is_active=True
                )
                return MembershipSerializer(membership).data
            except Membership.DoesNotExist:
                pass
        return None


class UsageMetricSerializer(serializers.ModelSerializer):
    usage_percentage = serializers.ReadOnlyField()
    is_near_limit = serializers.ReadOnlyField()
    is_over_limit = serializers.ReadOnlyField()

    class Meta:
        model = UsageMetric
        fields = [
            "id",
            "metric_name",
            "value",
            "limit",
            "usage_percentage",
            "is_near_limit",
            "is_over_limit",
            "period_start",
            "period_end",
        ]
        read_only_fields = ["id"]


class UsageSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageSnapshot
        fields = [
            "id",
            "organization",
            "metric_name",
            "value",
            "recorded_at",
        ]
        read_only_fields = ["id"]


class ActivityLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True, default=None)

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "organization",
            "user",
            "username",
            "action",
            "detail",
            "target_type",
            "target_id",
            "created_at",
        ]
        read_only_fields = fields


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True, default=None)
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "organization",
            "user",
            "username",
            "action",
            "action_display",
            "target_model",
            "target_id",
            "changes",
            "ip_address",
            "created_at",
        ]
        read_only_fields = fields


class BillingHistorySerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = BillingHistory
        fields = [
            "id",
            "organization",
            "description",
            "amount",
            "status",
            "status_display",
            "invoice_date",
            "invoice_number",
            "created_at",
        ]
        read_only_fields = fields


class PlanFeatureSerializer(serializers.ModelSerializer):
    plan_display = serializers.CharField(source="get_plan_display", read_only=True)

    class Meta:
        model = PlanFeature
        fields = [
            "id",
            "plan",
            "plan_display",
            "feature_name",
            "feature_value",
            "display_order",
            "is_highlighted",
        ]
        read_only_fields = ["id"]


class GlobalSettingSerializer(serializers.ModelSerializer):
    typed_value = serializers.SerializerMethodField()

    class Meta:
        model = GlobalSetting
        fields = [
            "id",
            "key",
            "value",
            "value_type",
            "description",
            "typed_value",
        ]
        read_only_fields = ["id"]

    def get_typed_value(self, obj):
        return obj.get_typed_value()
