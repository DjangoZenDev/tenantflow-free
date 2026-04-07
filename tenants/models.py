import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Organization(models.Model):
    PLAN_FREE = "free"
    PLAN_PRO = "pro"
    PLAN_ENTERPRISE = "enterprise"
    PLAN_CHOICES = [
        (PLAN_FREE, "Free"),
        (PLAN_PRO, "Pro"),
        (PLAN_ENTERPRISE, "Enterprise"),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_FREE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # Branding
    logo_url = models.URLField(max_length=500, blank=True, default="")
    primary_color = models.CharField(max_length=7, default="#10B981")
    secondary_color = models.CharField(max_length=7, default="#059669")
    sidebar_color = models.CharField(max_length=7, default="#FFFFFF")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.memberships.filter(is_active=True).count()

    @property
    def plan_display_color(self):
        colors = {
            self.PLAN_FREE: "gray",
            self.PLAN_PRO: "blue",
            self.PLAN_ENTERPRISE: "purple",
        }
        return colors.get(self.plan, "gray")

    def get_active_members(self):
        return User.objects.filter(
            memberships__organization=self,
            memberships__is_active=True,
        ).distinct()


class User(AbstractUser):
    ROLE_OWNER = "owner"
    ROLE_ADMIN = "admin"
    ROLE_MEMBER = "member"
    ROLE_VIEWER = "viewer"
    ROLE_CHOICES = [
        (ROLE_OWNER, "Owner"),
        (ROLE_ADMIN, "Admin"),
        (ROLE_MEMBER, "Member"),
        (ROLE_VIEWER, "Viewer"),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        related_name="members",
        null=True,
        blank=True,
        help_text="Currently active organization",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    avatar_color = models.CharField(max_length=7, default="#10B981")

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def initials(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.username[:2].upper()

    @property
    def role_badge_color(self):
        colors = {
            self.ROLE_OWNER: "red",
            self.ROLE_ADMIN: "orange",
            self.ROLE_MEMBER: "emerald",
            self.ROLE_VIEWER: "gray",
        }
        return colors.get(self.role, "gray")

    def get_orgs(self):
        return Organization.objects.filter(
            memberships__user=self,
            memberships__is_active=True,
            is_active=True,
        ).distinct()


class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=20, choices=User.ROLE_CHOICES, default=User.ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["user", "organization"]
        ordering = ["organization__name"]

    def __str__(self):
        return f"{self.user.username} @ {self.organization.name} ({self.get_role_display()})"

    @property
    def role_badge_color(self):
        colors = {
            User.ROLE_OWNER: "red",
            User.ROLE_ADMIN: "orange",
            User.ROLE_MEMBER: "emerald",
            User.ROLE_VIEWER: "gray",
        }
        return colors.get(self.role, "gray")


ROLE_HIERARCHY = {
    User.ROLE_OWNER: 4,
    User.ROLE_ADMIN: 3,
    User.ROLE_MEMBER: 2,
    User.ROLE_VIEWER: 1,
}


class Invitation(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="invitations"
    )
    email = models.EmailField()
    role = models.CharField(
        max_length=20, choices=User.ROLE_CHOICES, default=User.ROLE_MEMBER
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    accepted = models.BooleanField(default=False)
    invited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_invitations"
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invitation to {self.email} for {self.organization.name}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def is_valid(self):
        return not self.accepted and not self.revoked and not self.is_expired


class Subscription(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_PAST_DUE = "past_due"
    STATUS_CANCELED = "canceled"
    STATUS_TRIALING = "trialing"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_PAST_DUE, "Past Due"),
        (STATUS_CANCELED, "Canceled"),
        (STATUS_TRIALING, "Trialing"),
    ]

    organization = models.OneToOneField(
        Organization, on_delete=models.CASCADE, related_name="subscription"
    )
    plan = models.CharField(
        max_length=20,
        choices=Organization.PLAN_CHOICES,
        default=Organization.PLAN_FREE,
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE
    )
    current_period_start = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField(null=True, blank=True)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        ordering = ["-current_period_start"]

    def __str__(self):
        return f"{self.organization.name} - {self.get_plan_display()} ({self.get_status_display()})"

    @property
    def is_active(self):
        return self.status in (self.STATUS_ACTIVE, self.STATUS_TRIALING)


class UsageMetric(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="usage_metrics"
    )
    metric_name = models.CharField(max_length=100)
    value = models.IntegerField(default=0)
    limit = models.IntegerField(default=0)
    period_start = models.DateTimeField(default=timezone.now)
    period_end = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["metric_name"]
        unique_together = ["organization", "metric_name", "period_start"]

    def __str__(self):
        return f"{self.organization.name} - {self.metric_name}: {self.value}/{self.limit}"

    @property
    def usage_percentage(self):
        if self.limit == 0:
            return 0
        return min(round((self.value / self.limit) * 100, 1), 100)

    @property
    def is_near_limit(self):
        return self.usage_percentage >= 80

    @property
    def is_over_limit(self):
        return self.usage_percentage >= 100


class UsageSnapshot(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="usage_snapshots"
    )
    metric_name = models.CharField(max_length=100)
    value = models.IntegerField(default=0)
    recorded_at = models.DateField()

    class Meta:
        ordering = ["recorded_at"]
        unique_together = ["organization", "metric_name", "recorded_at"]

    def __str__(self):
        return f"{self.organization.name} - {self.metric_name}: {self.value} @ {self.recorded_at}"


class ActivityLog(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="activities"
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    detail = models.TextField(blank=True, default="")
    target_type = models.CharField(max_length=100, blank=True, default="")
    target_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.action} by {self.user} in {self.organization}"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Created"),
        ("update", "Updated"),
        ("delete", "Deleted"),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="audit_logs"
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    target_model = models.CharField(max_length=100)
    target_id = models.IntegerField(null=True, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "-created_at"]),
            models.Index(fields=["target_model", "target_id"]),
        ]

    def __str__(self):
        return f"{self.get_action_display()} {self.target_model} by {self.user}"


class BillingHistory(models.Model):
    STATUS_CHOICES = [
        ("paid", "Paid"),
        ("pending", "Pending"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="billing_history"
    )
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="paid")
    invoice_date = models.DateField()
    invoice_number = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-invoice_date"]
        verbose_name_plural = "Billing history"

    def __str__(self):
        return f"{self.invoice_number} - {self.organization.name} - ${self.amount}"


class PlanFeature(models.Model):
    plan = models.CharField(max_length=20, choices=Organization.PLAN_CHOICES)
    feature_name = models.CharField(max_length=200)
    feature_value = models.CharField(max_length=200)
    display_order = models.IntegerField(default=0)
    is_highlighted = models.BooleanField(default=False)

    class Meta:
        ordering = ["plan", "display_order"]
        unique_together = ["plan", "feature_name"]

    def __str__(self):
        return f"{self.get_plan_display()} - {self.feature_name}: {self.feature_value}"


class GlobalSetting(models.Model):
    VALUE_TYPE_CHOICES = [
        ("string", "String"),
        ("boolean", "Boolean"),
        ("integer", "Integer"),
        ("json", "JSON"),
    ]

    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True, default="")
    value_type = models.CharField(max_length=10, choices=VALUE_TYPE_CHOICES, default="string")
    description = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return f"{self.key} = {self.value}"

    def get_typed_value(self):
        if self.value_type == "boolean":
            return self.value.lower() in ("true", "1", "yes")
        elif self.value_type == "integer":
            try:
                return int(self.value)
            except (ValueError, TypeError):
                return 0
        elif self.value_type == "json":
            import json
            try:
                return json.loads(self.value)
            except (json.JSONDecodeError, TypeError):
                return {}
        return self.value
