import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from tenants.models import (
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


class Command(BaseCommand):
    help = "Seeds the database with sample data for TenantFlow Pro."

    def handle(self, *args, **options):
        self.stdout.write("Seeding TenantFlow Pro database...")

        # Clear data
        UsageSnapshot.objects.all().delete()
        ActivityLog.objects.all().delete()
        AuditLog.objects.all().delete()
        BillingHistory.objects.all().delete()
        PlanFeature.objects.all().delete()
        GlobalSetting.objects.all().delete()
        Invitation.objects.all().delete()
        Membership.objects.all().delete()
        UsageMetric.objects.all().delete()
        Subscription.objects.all().delete()

        # Create Organizations with branding
        orgs_data = [
            {
                "name": "Acme Corporation",
                "slug": "acme-corp",
                "plan": "enterprise",
                "primary_color": "#6366F1",
                "secondary_color": "#4F46E5",
                "sidebar_color": "#FFFFFF",
            },
            {
                "name": "Startup Labs",
                "slug": "startup-labs",
                "plan": "pro",
                "primary_color": "#10B981",
                "secondary_color": "#059669",
                "sidebar_color": "#FFFFFF",
            },
            {
                "name": "DevTeam Inc",
                "slug": "devteam-inc",
                "plan": "free",
                "primary_color": "#3B82F6",
                "secondary_color": "#2563EB",
                "sidebar_color": "#F8FAFC",
            },
            {
                "name": "CloudNine Solutions",
                "slug": "cloudnine",
                "plan": "pro",
                "primary_color": "#8B5CF6",
                "secondary_color": "#7C3AED",
                "sidebar_color": "#FFFFFF",
            },
        ]

        orgs = []
        for od in orgs_data:
            org, _ = Organization.objects.update_or_create(slug=od["slug"], defaults=od)
            orgs.append(org)
        self.stdout.write(self.style.SUCCESS(f"  Created {len(orgs)} organizations"))

        # Create superuser
        if not User.objects.filter(username="admin").exists():
            admin_user = User.objects.create_superuser(
                username="admin",
                email="admin@tenantflow.dev",
                password="admin123",
                first_name="Admin",
                last_name="User",
                organization=orgs[0],
                role="owner",
                avatar_color="#6366F1",
            )
        else:
            admin_user = User.objects.get(username="admin")
            admin_user.organization = orgs[0]
            admin_user.save()
        self.stdout.write(self.style.SUCCESS("  Superuser: admin / admin123"))

        # Create sample users with org assignments
        users_data = [
            # Acme Corp
            ("sarah.chen", "Sarah", "Chen", orgs[0], "owner", "#EF4444"),
            ("mike.johnson", "Mike", "Johnson", orgs[0], "admin", "#F59E0B"),
            ("emma.wilson", "Emma", "Wilson", orgs[0], "member", "#10B981"),
            ("james.brown", "James", "Brown", orgs[0], "member", "#3B82F6"),
            ("lisa.garcia", "Lisa", "Garcia", orgs[0], "viewer", "#8B5CF6"),
            # Startup Labs
            ("alex.turner", "Alex", "Turner", orgs[1], "owner", "#EC4899"),
            ("priya.patel", "Priya", "Patel", orgs[1], "admin", "#14B8A6"),
            ("ryan.kim", "Ryan", "Kim", orgs[1], "member", "#F97316"),
            # DevTeam Inc
            ("tom.baker", "Tom", "Baker", orgs[2], "owner", "#6366F1"),
            ("nina.rodriguez", "Nina", "Rodriguez", orgs[2], "member", "#10B981"),
            # CloudNine
            ("dave.murphy", "Dave", "Murphy", orgs[3], "owner", "#8B5CF6"),
            ("jenna.lee", "Jenna", "Lee", orgs[3], "admin", "#EC4899"),
            ("carlos.silva", "Carlos", "Silva", orgs[3], "member", "#3B82F6"),
        ]

        all_users = [admin_user]
        for username, first, last, org, role, color in users_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "email": f"{username}@tenantflow.dev",
                    "organization": org,
                    "role": role,
                    "avatar_color": color,
                },
            )
            if created:
                user.set_password("testpass123")
                user.save()
            all_users.append(user)

        self.stdout.write(self.style.SUCCESS(f"  Created {len(users_data)} users"))

        # Create Memberships (primary memberships)
        Membership.objects.update_or_create(
            user=admin_user, organization=orgs[0],
            defaults={"role": "owner", "is_active": True},
        )
        for username, first, last, org, role, color in users_data:
            user = User.objects.get(username=username)
            Membership.objects.update_or_create(
                user=user, organization=org,
                defaults={"role": role, "is_active": True},
            )

        # Multi-org memberships (some users belong to multiple orgs)
        cross_memberships = [
            ("sarah.chen", orgs[1], "viewer"),
            ("alex.turner", orgs[0], "member"),
            ("admin", orgs[1], "admin"),
            ("admin", orgs[2], "viewer"),
        ]
        for username, org, role in cross_memberships:
            user = User.objects.get(username=username)
            Membership.objects.update_or_create(
                user=user, organization=org,
                defaults={"role": role, "is_active": True},
            )
        self.stdout.write(self.style.SUCCESS(f"  Created memberships (including {len(cross_memberships)} cross-org)"))

        # Create Subscriptions
        plan_prices = {"free": Decimal("0"), "pro": Decimal("29"), "enterprise": Decimal("99")}
        now = timezone.now()
        for org in orgs:
            Subscription.objects.update_or_create(
                organization=org,
                defaults={
                    "plan": org.plan,
                    "status": "active",
                    "monthly_price": plan_prices[org.plan],
                    "current_period_start": now - timedelta(days=15),
                    "current_period_end": now + timedelta(days=15),
                },
            )
        self.stdout.write(self.style.SUCCESS("  Created subscriptions"))

        # Create Usage Metrics
        plan_limits = {
            "free": {"API Calls": 1000, "Storage (MB)": 500, "Team Members": 5},
            "pro": {"API Calls": 50000, "Storage (MB)": 10240, "Team Members": 25},
            "enterprise": {"API Calls": 1000000, "Storage (MB)": 102400, "Team Members": 1000},
        }
        for org in orgs:
            limits = plan_limits[org.plan]
            for metric_name, limit in limits.items():
                usage_pct = random.randint(20, 90) / 100
                UsageMetric.objects.update_or_create(
                    organization=org,
                    metric_name=metric_name,
                    period_start=now - timedelta(days=30),
                    defaults={
                        "value": int(limit * usage_pct),
                        "limit": limit,
                        "period_end": now,
                    },
                )
        self.stdout.write(self.style.SUCCESS("  Created usage metrics"))

        # Create Usage Snapshots (30 days of trend data)
        snapshot_count = 0
        for org in orgs:
            limits = plan_limits[org.plan]
            for metric_name, limit in limits.items():
                base_pct = random.uniform(0.3, 0.6)
                for day in range(30):
                    date = (now - timedelta(days=30 - day)).date()
                    daily_pct = base_pct + (day / 30) * 0.3 + random.uniform(-0.05, 0.05)
                    value = int(limit * min(daily_pct, 0.95))
                    UsageSnapshot.objects.update_or_create(
                        organization=org,
                        metric_name=metric_name,
                        recorded_at=date,
                        defaults={"value": value},
                    )
                    snapshot_count += 1
        self.stdout.write(self.style.SUCCESS(f"  Created {snapshot_count} usage snapshots"))

        # Create Plan Features
        features_data = [
            ("free", "Up to 5 team members", 1, False),
            ("free", "1,000 API calls/month", 2, False),
            ("free", "500 MB storage", 3, False),
            ("free", "Community support", 4, False),
            ("free", "Basic analytics", 5, False),
            ("pro", "Up to 25 team members", 1, True),
            ("pro", "50,000 API calls/month", 2, True),
            ("pro", "10 GB storage", 3, False),
            ("pro", "Priority email support", 4, False),
            ("pro", "Advanced analytics", 5, True),
            ("pro", "Custom integrations", 6, False),
            ("pro", "API access", 7, False),
            ("enterprise", "Unlimited team members", 1, True),
            ("enterprise", "Unlimited API calls", 2, True),
            ("enterprise", "100 GB storage", 3, False),
            ("enterprise", "24/7 dedicated support", 4, True),
            ("enterprise", "SSO & SAML", 5, True),
            ("enterprise", "Custom contracts", 6, False),
            ("enterprise", "SLA guarantee", 7, False),
            ("enterprise", "Audit logging", 8, False),
        ]
        for plan, feature_value, order, highlighted in features_data:
            PlanFeature.objects.update_or_create(
                plan=plan,
                feature_name=feature_value,
                defaults={
                    "feature_value": feature_value,
                    "display_order": order,
                    "is_highlighted": highlighted,
                },
            )
        self.stdout.write(self.style.SUCCESS(f"  Created {len(features_data)} plan features"))

        # Create Billing History
        billing_count = 0
        for org in orgs:
            if org.plan == "free":
                continue
            price = plan_prices[org.plan]
            for month in range(3):
                date = (now - timedelta(days=30 * month)).date()
                BillingHistory.objects.update_or_create(
                    invoice_number=f"INV-{org.slug}-{date.strftime('%Y%m')}",
                    defaults={
                        "organization": org,
                        "description": f"{org.get_plan_display()} Plan - {date.strftime('%B %Y')}",
                        "amount": price,
                        "status": "paid",
                        "invoice_date": date,
                    },
                )
                billing_count += 1
        self.stdout.write(self.style.SUCCESS(f"  Created {billing_count} billing records"))

        # Create Activity Log entries
        activity_actions = [
            ("invited_member", "Invited {email} as {role}"),
            ("updated_settings", "Updated organization settings"),
            ("changed_plan", "Upgraded plan to {plan}"),
            ("removed_member", "Removed {name} from the team"),
            ("updated_branding", "Updated organization branding"),
            ("exported_data", "Exported usage data"),
            ("created_api_key", "Created a new API key"),
        ]
        activity_count = 0
        for org in orgs:
            org_members = list(Membership.objects.filter(organization=org).select_related("user"))
            for i in range(random.randint(8, 15)):
                action, detail_tpl = random.choice(activity_actions)
                member = random.choice(org_members) if org_members else None
                detail = detail_tpl.format(
                    email=f"user{random.randint(1, 99)}@example.com",
                    role=random.choice(["member", "admin", "viewer"]),
                    plan=random.choice(["Pro", "Enterprise"]),
                    name=member.user.get_full_name() if member else "Unknown",
                )
                ActivityLog.objects.create(
                    organization=org,
                    user=member.user if member else None,
                    action=action,
                    detail=detail,
                    created_at=now - timedelta(hours=random.randint(1, 168)),
                )
                activity_count += 1
        self.stdout.write(self.style.SUCCESS(f"  Created {activity_count} activity log entries"))

        # Create Invitations
        invitations_data = [
            (orgs[0], "newdev@example.com", "member"),
            (orgs[0], "contractor@example.com", "viewer"),
            (orgs[1], "designer@example.com", "member"),
        ]
        for org, email, role in invitations_data:
            org_members = Membership.objects.filter(organization=org, role__in=["owner", "admin"]).select_related("user")
            inviter = org_members.first().user if org_members.exists() else admin_user
            Invitation.objects.create(
                organization=org, email=email, role=role, invited_by=inviter,
            )
        self.stdout.write(self.style.SUCCESS(f"  Created {len(invitations_data)} invitations"))

        # Create Global Settings
        settings_data = [
            ("site_name", "TenantFlow", "string", "The name of the platform"),
            ("max_orgs_per_user", "5", "integer", "Maximum organizations a user can belong to"),
            ("allow_signups", "true", "boolean", "Whether new user signups are allowed"),
            ("maintenance_mode", "false", "boolean", "Enable maintenance mode"),
            ("default_plan", "free", "string", "Default plan for new organizations"),
        ]
        for key, value, vtype, desc in settings_data:
            GlobalSetting.objects.update_or_create(
                key=key, defaults={"value": value, "value_type": vtype, "description": desc},
            )
        self.stdout.write(self.style.SUCCESS(f"  Created {len(settings_data)} global settings"))

        self.stdout.write(self.style.SUCCESS("\nTenantFlow Pro seeding complete!"))
        self.stdout.write("Login credentials:")
        self.stdout.write("  admin / admin123 (Superuser, Acme Corp owner)")
        self.stdout.write("  sarah.chen / testpass123 (Acme Corp owner)")
        self.stdout.write("  alex.turner / testpass123 (Startup Labs owner)")
        self.stdout.write("  tom.baker / testpass123 (DevTeam Inc owner)")
        self.stdout.write("  lisa.garcia / testpass123 (Acme Corp viewer)")
