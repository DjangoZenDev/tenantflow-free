import json
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .emails import send_invitation_email
from .logging import log_activity, log_audit
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
from .permissions import require_role


@login_required
def tenant_dashboard(request):
    org = request.organization
    if not org:
        return render(request, "tenants/no_org.html")

    usage_metrics = UsageMetric.objects.filter(organization=org)
    memberships = Membership.objects.filter(
        organization=org, is_active=True
    ).select_related("user")[:5]
    member_count = Membership.objects.filter(organization=org, is_active=True).count()
    pending_invites = Invitation.objects.filter(
        organization=org, accepted=False, revoked=False
    ).count()
    recent_activities = ActivityLog.objects.filter(organization=org).select_related(
        "user"
    )[:10]

    try:
        subscription = org.subscription
    except Subscription.DoesNotExist:
        subscription = None

    context = {
        "org": org,
        "usage_metrics": usage_metrics,
        "team_members": memberships,
        "member_count": member_count,
        "pending_invites": pending_invites,
        "subscription": subscription,
        "recent_activities": recent_activities,
    }
    return render(request, "tenants/dashboard.html", context)


@login_required
def team_members(request):
    org = request.organization
    if not org:
        return render(request, "tenants/no_org.html")

    memberships = (
        Membership.objects.filter(organization=org, is_active=True)
        .select_related("user")
        .order_by("role", "user__first_name")
    )
    pending_invites = Invitation.objects.filter(
        organization=org, accepted=False, revoked=False
    )

    context = {
        "org": org,
        "members": memberships,
        "pending_invites": pending_invites,
    }

    if request.headers.get("HX-Request"):
        return render(request, "tenants/partials/team_list.html", context)

    return render(request, "tenants/team.html", context)


@login_required
@require_role("owner", "admin")
def invite_member(request):
    org = request.organization
    if not org:
        return render(request, "tenants/no_org.html")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        role = request.POST.get("role", User.ROLE_MEMBER)

        if email:
            existing = Invitation.objects.filter(
                organization=org, email=email, accepted=False, revoked=False
            ).exists()
            if existing:
                messages.warning(request, f"An invitation for {email} already exists.")
            else:
                invitation = Invitation.objects.create(
                    organization=org,
                    email=email,
                    role=role,
                    invited_by=request.user,
                )
                send_invitation_email(invitation)
                log_activity(
                    request,
                    "invited_member",
                    detail=f"Invited {email} as {role}",
                    target_type="Invitation",
                    target_id=invitation.pk,
                )
                messages.success(request, f"Invitation sent to {email}.")
        else:
            messages.error(request, "Please enter a valid email address.")

        if request.headers.get("HX-Request"):
            memberships = (
                Membership.objects.filter(organization=org, is_active=True)
                .select_related("user")
                .order_by("role", "user__first_name")
            )
            pending_invites = Invitation.objects.filter(
                organization=org, accepted=False, revoked=False
            )
            return render(
                request,
                "tenants/partials/team_list.html",
                {"org": org, "members": memberships, "pending_invites": pending_invites},
            )

        return redirect("team_members")

    context = {"org": org, "role_choices": User.ROLE_CHOICES}
    if request.headers.get("HX-Request"):
        return render(request, "tenants/partials/invite_form.html", context)
    return render(request, "tenants/partials/invite_form.html", context)


@login_required
def usage_overview(request):
    org = request.organization
    if not org:
        return render(request, "tenants/no_org.html")

    usage_metrics = UsageMetric.objects.filter(organization=org)

    # Get usage snapshots for charts (last 30 days)
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    snapshots = UsageSnapshot.objects.filter(
        organization=org, recorded_at__gte=thirty_days_ago
    ).order_by("recorded_at")

    # Build chart data grouped by metric name
    chart_data = {}
    for snapshot in snapshots:
        if snapshot.metric_name not in chart_data:
            chart_data[snapshot.metric_name] = {"labels": [], "values": []}
        chart_data[snapshot.metric_name]["labels"].append(
            snapshot.recorded_at.strftime("%Y-%m-%d")
        )
        chart_data[snapshot.metric_name]["values"].append(snapshot.value)

    context = {
        "org": org,
        "usage_metrics": usage_metrics,
        "chart_data_json": json.dumps(chart_data),
    }

    if request.headers.get("HX-Request"):
        return render(request, "tenants/partials/usage_bars.html", context)

    return render(request, "tenants/usage.html", context)


@login_required
def billing_view(request):
    org = request.organization
    if not org:
        return render(request, "tenants/no_org.html")

    try:
        subscription = org.subscription
    except Subscription.DoesNotExist:
        subscription = None

    # Try to load plan features from the database
    db_features = PlanFeature.objects.all().order_by("plan", "display_order")

    if db_features.exists():
        plans_dict = {}
        plan_meta = {
            "free": {"name": "Free", "price": "$0", "color": "gray"},
            "pro": {"name": "Pro", "price": "$29", "color": "blue"},
            "enterprise": {"name": "Enterprise", "price": "$99", "color": "purple"},
        }
        for feature in db_features:
            if feature.plan not in plans_dict:
                meta = plan_meta.get(feature.plan, {"name": feature.plan, "price": "N/A", "color": "gray"})
                plans_dict[feature.plan] = {
                    "name": meta["name"],
                    "slug": feature.plan,
                    "price": meta["price"],
                    "color": meta["color"],
                    "features": [],
                }
            plans_dict[feature.plan]["features"].append(feature.feature_value)
        plans = list(plans_dict.values())
    else:
        # Fallback to hardcoded plans
        plans = [
            {
                "name": "Free",
                "slug": "free",
                "price": "$0",
                "color": "gray",
                "features": [
                    "Up to 5 team members",
                    "1,000 API calls/month",
                    "500 MB storage",
                    "Community support",
                ],
            },
            {
                "name": "Pro",
                "slug": "pro",
                "price": "$29",
                "color": "blue",
                "features": [
                    "Up to 25 team members",
                    "50,000 API calls/month",
                    "10 GB storage",
                    "Priority support",
                    "Advanced analytics",
                    "Custom integrations",
                ],
            },
            {
                "name": "Enterprise",
                "slug": "enterprise",
                "price": "$99",
                "color": "purple",
                "features": [
                    "Unlimited team members",
                    "Unlimited API calls",
                    "100 GB storage",
                    "24/7 dedicated support",
                    "SSO & SAML",
                    "Custom contracts",
                    "SLA guarantee",
                ],
            },
        ]

    billing_history = BillingHistory.objects.filter(organization=org)[:20]

    context = {
        "org": org,
        "subscription": subscription,
        "plans": plans,
        "billing_history": billing_history,
    }
    return render(request, "tenants/billing.html", context)


@login_required
@require_role("owner", "admin")
def organization_settings(request):
    org = request.organization
    if not org:
        return render(request, "tenants/no_org.html")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            org.name = name

        # Handle branding fields
        logo_url = request.POST.get("logo_url", "").strip()
        primary_color = request.POST.get("primary_color", "").strip()
        secondary_color = request.POST.get("secondary_color", "").strip()
        sidebar_color = request.POST.get("sidebar_color", "").strip()

        if logo_url is not None:
            org.logo_url = logo_url
        if primary_color:
            org.primary_color = primary_color
        if secondary_color:
            org.secondary_color = secondary_color
        if sidebar_color:
            org.sidebar_color = sidebar_color

        org.save()
        log_activity(
            request,
            "updated_settings",
            detail="Updated organization settings",
            target_type="Organization",
            target_id=org.pk,
        )
        messages.success(request, "Organization settings updated.")
        return redirect("organization_settings")

    context = {"org": org}
    return render(request, "tenants/settings.html", context)


@login_required
def switch_organization(request):
    if request.method == "POST":
        org_id = request.POST.get("organization_id")
        if org_id:
            org = get_object_or_404(Organization, id=org_id, is_active=True)
            # Verify membership via Membership model
            has_membership = Membership.objects.filter(
                user=request.user, organization=org, is_active=True
            ).exists()
            if has_membership:
                request.user.organization = org
                request.user.save()
                messages.success(request, f"Switched to {org.name}.")
            else:
                messages.error(request, "You do not have access to that organization.")
        return redirect("tenant_dashboard")

    # GET: list available orgs for this user via Membership
    user_orgs = Organization.objects.filter(
        memberships__user=request.user,
        memberships__is_active=True,
        is_active=True,
    ).distinct()

    context = {
        "user_orgs": user_orgs,
        "current_org": request.organization,
    }
    return render(request, "tenants/switch_org.html", context)


def accept_invitation(request, token):
    """
    GET: Show invitation info (no login required).
    POST: Requires login, creates Membership, marks invite accepted.
    """
    invitation = get_object_or_404(Invitation, token=token)

    if not invitation.is_valid:
        return render(request, "tenants/invitation_invalid.html", {
            "invitation": invitation,
        })

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to accept this invitation.")
            return redirect(f"/login/?next=/invitations/{token}/accept/")

        # Create membership
        membership, created = Membership.objects.get_or_create(
            user=request.user,
            organization=invitation.organization,
            defaults={"role": invitation.role, "is_active": True},
        )
        if not created:
            membership.role = invitation.role
            membership.is_active = True
            membership.save()

        # Mark invitation as accepted
        invitation.accepted = True
        invitation.accepted_at = timezone.now()
        invitation.save()

        # Set user's active organization
        request.user.organization = invitation.organization
        request.user.save()

        messages.success(
            request,
            f"You've joined {invitation.organization.name} as a {invitation.get_role_display()}.",
        )
        return redirect("tenant_dashboard")

    # GET: show invitation info
    return render(request, "tenants/accept_invitation.html", {
        "invitation": invitation,
        "org": invitation.organization,
    })


@login_required
@require_role("owner", "admin")
@require_POST
def resend_invitation(request, pk):
    """Resend an invitation email and reset its expiration."""
    org = request.organization
    invitation = get_object_or_404(
        Invitation, pk=pk, organization=org, accepted=False, revoked=False
    )

    invitation.expires_at = timezone.now() + timedelta(days=7)
    invitation.save()
    send_invitation_email(invitation)

    log_activity(
        request,
        "resent_invitation",
        detail=f"Resent invitation to {invitation.email}",
        target_type="Invitation",
        target_id=invitation.pk,
    )
    messages.success(request, f"Invitation resent to {invitation.email}.")

    if request.headers.get("HX-Request"):
        memberships = (
            Membership.objects.filter(organization=org, is_active=True)
            .select_related("user")
            .order_by("role", "user__first_name")
        )
        pending_invites = Invitation.objects.filter(
            organization=org, accepted=False, revoked=False
        )
        return render(
            request,
            "tenants/partials/team_list.html",
            {"org": org, "members": memberships, "pending_invites": pending_invites},
        )

    return redirect("team_members")


@login_required
@require_role("owner", "admin")
@require_POST
def revoke_invitation(request, pk):
    """Revoke a pending invitation."""
    org = request.organization
    invitation = get_object_or_404(
        Invitation, pk=pk, organization=org, accepted=False
    )

    invitation.revoked = True
    invitation.save()

    log_activity(
        request,
        "revoked_invitation",
        detail=f"Revoked invitation for {invitation.email}",
        target_type="Invitation",
        target_id=invitation.pk,
    )
    messages.success(request, f"Invitation for {invitation.email} has been revoked.")

    if request.headers.get("HX-Request"):
        memberships = (
            Membership.objects.filter(organization=org, is_active=True)
            .select_related("user")
            .order_by("role", "user__first_name")
        )
        pending_invites = Invitation.objects.filter(
            organization=org, accepted=False, revoked=False
        )
        return render(
            request,
            "tenants/partials/team_list.html",
            {"org": org, "members": memberships, "pending_invites": pending_invites},
        )

    return redirect("team_members")


@login_required
def upgrade_plan(request):
    """Show plan upgrade confirmation and handle plan changes."""
    org = request.organization
    if not org:
        return render(request, "tenants/no_org.html")

    plan_prices = {
        Organization.PLAN_FREE: Decimal("0.00"),
        Organization.PLAN_PRO: Decimal("29.00"),
        Organization.PLAN_ENTERPRISE: Decimal("99.00"),
    }

    if request.method == "POST":
        new_plan = request.POST.get("plan", "").strip()
        if new_plan not in dict(Organization.PLAN_CHOICES):
            messages.error(request, "Invalid plan selected.")
            return redirect("billing_view")

        old_plan = org.plan
        org.plan = new_plan
        org.save()

        # Update or create Subscription
        subscription, created = Subscription.objects.get_or_create(
            organization=org,
            defaults={
                "plan": new_plan,
                "status": Subscription.STATUS_ACTIVE,
                "monthly_price": plan_prices.get(new_plan, Decimal("0.00")),
                "current_period_start": timezone.now(),
                "current_period_end": timezone.now() + timedelta(days=30),
            },
        )
        if not created:
            subscription.plan = new_plan
            subscription.status = Subscription.STATUS_ACTIVE
            subscription.monthly_price = plan_prices.get(new_plan, Decimal("0.00"))
            subscription.current_period_start = timezone.now()
            subscription.current_period_end = timezone.now() + timedelta(days=30)
            subscription.save()

        # Create billing history entry
        BillingHistory.objects.create(
            organization=org,
            description=f"Plan change: {old_plan} -> {new_plan}",
            amount=plan_prices.get(new_plan, Decimal("0.00")),
            status="paid",
            invoice_date=timezone.now().date(),
            invoice_number=f"INV-{org.pk}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
        )

        log_activity(
            request,
            "upgraded_plan",
            detail=f"Changed plan from {old_plan} to {new_plan}",
            target_type="Organization",
            target_id=org.pk,
        )

        messages.success(
            request,
            f"Plan updated to {org.get_plan_display()}.",
        )
        return redirect("billing_view")

    # GET: show confirmation page
    context = {
        "org": org,
        "plan_choices": Organization.PLAN_CHOICES,
        "plan_prices": plan_prices,
    }
    return render(request, "tenants/upgrade_plan.html", context)


@login_required
@require_role("owner", "admin")
def audit_log_view(request):
    """Paginated audit log with filtering by action type."""
    org = request.organization
    if not org:
        return render(request, "tenants/no_org.html")

    logs = AuditLog.objects.filter(organization=org).select_related("user")

    # Filter by action type
    action_filter = request.GET.get("action", "")
    if action_filter:
        logs = logs.filter(action=action_filter)

    # Filter by target model
    model_filter = request.GET.get("model", "")
    if model_filter:
        logs = logs.filter(target_model=model_filter)

    paginator = Paginator(logs, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "org": org,
        "page_obj": page_obj,
        "action_filter": action_filter,
        "model_filter": model_filter,
        "action_choices": AuditLog.ACTION_CHOICES,
    }
    return render(request, "tenants/audit_log.html", context)


@login_required
def global_settings_view(request):
    """List and edit GlobalSetting entries. Superuser only."""
    if not request.user.is_superuser:
        return render(request, "tenants/forbidden.html", status=403)

    if request.method == "POST":
        key = request.POST.get("key", "").strip()
        value = request.POST.get("value", "").strip()
        value_type = request.POST.get("value_type", "string").strip()
        description = request.POST.get("description", "").strip()

        if key:
            setting, created = GlobalSetting.objects.update_or_create(
                key=key,
                defaults={
                    "value": value,
                    "value_type": value_type,
                    "description": description,
                },
            )
            action = "Created" if created else "Updated"
            messages.success(request, f"{action} setting '{key}'.")
        else:
            messages.error(request, "Setting key is required.")

        return redirect("global_settings")

    settings_list = GlobalSetting.objects.all()
    context = {
        "settings_list": settings_list,
        "value_type_choices": GlobalSetting.VALUE_TYPE_CHOICES,
    }
    return render(request, "tenants/global_settings.html", context)


@login_required
def usage_chart_data(request):
    """JSON endpoint returning usage snapshots for Chart.js."""
    org = request.organization
    if not org:
        return JsonResponse({"error": "No organization"}, status=400)

    days = int(request.GET.get("days", 30))
    start_date = timezone.now().date() - timedelta(days=days)

    snapshots = UsageSnapshot.objects.filter(
        organization=org, recorded_at__gte=start_date
    ).order_by("recorded_at")

    chart_data = {}
    for snapshot in snapshots:
        if snapshot.metric_name not in chart_data:
            chart_data[snapshot.metric_name] = {"labels": [], "values": []}
        chart_data[snapshot.metric_name]["labels"].append(
            snapshot.recorded_at.strftime("%Y-%m-%d")
        )
        chart_data[snapshot.metric_name]["values"].append(snapshot.value)

    return JsonResponse(chart_data)
