from .models import Membership, Organization


def tenant_branding(request):
    """Inject tenant branding and membership info into all templates."""
    context = {
        "brand_primary": "#10B981",
        "brand_secondary": "#059669",
        "brand_sidebar": "#FFFFFF",
        "brand_logo_url": "",
        "user_membership": None,
        "user_role": None,
        "user_orgs": [],
        "is_owner": False,
        "is_admin_or_owner": False,
    }

    if not hasattr(request, "user") or not request.user.is_authenticated:
        return context

    org = getattr(request, "organization", None)

    if org:
        context["brand_primary"] = org.primary_color
        context["brand_secondary"] = org.secondary_color
        context["brand_sidebar"] = org.sidebar_color
        context["brand_logo_url"] = org.logo_url

    membership = getattr(request, "membership", None)
    if membership:
        context["user_membership"] = membership
        context["user_role"] = membership.role
        context["is_owner"] = membership.role == "owner"
        context["is_admin_or_owner"] = membership.role in ("owner", "admin")

    context["user_orgs"] = list(
        Organization.objects.filter(
            memberships__user=request.user,
            memberships__is_active=True,
            is_active=True,
        ).distinct()
    )

    return context
