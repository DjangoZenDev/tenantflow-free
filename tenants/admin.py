from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    ActivityLog,
    AuditLog,
    BillingHistory,
    GlobalSetting,
    Invitation,
    Membership,
    Organization,
    PlanFeature,
    Subscription,
    UsageMetric,
    UsageSnapshot,
    User,
)


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0
    fields = ["user", "role", "is_active", "joined_at"]
    readonly_fields = ["joined_at"]


class MembershipUserInline(admin.TabularInline):
    model = Membership
    extra = 0
    fields = ["organization", "role", "is_active", "joined_at"]
    readonly_fields = ["joined_at"]
    verbose_name = "Organization membership"
    verbose_name_plural = "Organization memberships"


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "plan", "is_active", "member_count", "created_at"]
    list_filter = ["plan", "is_active"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [MembershipInline]
    fieldsets = (
        (None, {"fields": ("name", "slug", "plan", "is_active")}),
        (
            "Branding",
            {
                "fields": (
                    "logo_url",
                    "primary_color",
                    "secondary_color",
                    "sidebar_color",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "organization", "role", "is_active"]
    list_filter = ["role", "organization", "is_active"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Tenant Info", {"fields": ("organization", "role", "avatar_color")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Tenant Info", {"fields": ("organization", "role")}),
    )
    inlines = [MembershipUserInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "organization", "role", "is_active", "joined_at"]
    list_filter = ["role", "is_active", "organization"]
    search_fields = ["user__username", "user__email", "organization__name"]
    raw_id_fields = ["user", "organization"]


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "organization",
        "role",
        "invited_by",
        "accepted",
        "revoked",
        "expires_at",
        "created_at",
    ]
    list_filter = ["accepted", "revoked", "role"]
    search_fields = ["email", "organization__name"]
    readonly_fields = ["token"]
    raw_id_fields = ["invited_by"]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "organization",
        "plan",
        "status",
        "monthly_price",
        "current_period_start",
        "current_period_end",
    ]
    list_filter = ["plan", "status"]


@admin.register(UsageMetric)
class UsageMetricAdmin(admin.ModelAdmin):
    list_display = [
        "organization",
        "metric_name",
        "value",
        "limit",
        "usage_percentage",
        "period_start",
    ]
    list_filter = ["metric_name", "organization"]


@admin.register(UsageSnapshot)
class UsageSnapshotAdmin(admin.ModelAdmin):
    list_display = ["organization", "metric_name", "value", "recorded_at"]
    list_filter = ["metric_name", "organization"]
    date_hierarchy = "recorded_at"


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ["organization", "user", "action", "target_type", "created_at"]
    list_filter = ["action", "organization", "target_type"]
    search_fields = ["action", "detail", "user__username"]
    readonly_fields = [
        "organization",
        "user",
        "action",
        "detail",
        "target_type",
        "target_id",
        "created_at",
    ]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "organization",
        "user",
        "action",
        "target_model",
        "target_id",
        "ip_address",
        "created_at",
    ]
    list_filter = ["action", "target_model", "organization"]
    search_fields = ["target_model", "user__username", "ip_address"]
    readonly_fields = [
        "organization",
        "user",
        "action",
        "target_model",
        "target_id",
        "changes",
        "ip_address",
        "created_at",
    ]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(BillingHistory)
class BillingHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "invoice_number",
        "organization",
        "description",
        "amount",
        "status",
        "invoice_date",
    ]
    list_filter = ["status", "organization"]
    search_fields = ["invoice_number", "description", "organization__name"]
    date_hierarchy = "invoice_date"


@admin.register(PlanFeature)
class PlanFeatureAdmin(admin.ModelAdmin):
    list_display = ["plan", "feature_name", "feature_value", "display_order", "is_highlighted"]
    list_filter = ["plan", "is_highlighted"]
    search_fields = ["feature_name", "feature_value"]
    ordering = ["plan", "display_order"]


@admin.register(GlobalSetting)
class GlobalSettingAdmin(admin.ModelAdmin):
    list_display = ["key", "value", "value_type", "description"]
    list_filter = ["value_type"]
    search_fields = ["key", "description"]
