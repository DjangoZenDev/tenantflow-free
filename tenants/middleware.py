from django.utils.deprecation import MiddlewareMixin

from .models import Membership, Organization


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware that attaches the current organization and membership to the request.

    For authenticated users:
    - Checks X-Tenant-Org header first (slug-based org switching)
    - Falls back to user.organization
    - Looks up Membership for the user+org pair
    - If org exists but no valid Membership, clears request.organization

    Unauthenticated users get request.organization = None and request.membership = None.
    """

    def process_request(self, request):
        request.organization = None
        request.membership = None

        if not hasattr(request, "user") or not request.user.is_authenticated:
            return

        organization = None
        membership = None

        # Check for X-Tenant-Org header (slug-based org override)
        tenant_slug = request.META.get("HTTP_X_TENANT_ORG")
        if tenant_slug:
            try:
                organization = Organization.objects.get(
                    slug=tenant_slug, is_active=True
                )
            except Organization.DoesNotExist:
                organization = None

        # Fall back to user's current organization
        if not organization:
            organization = getattr(request.user, "organization", None)
            if organization and not organization.is_active:
                organization = None

        # Verify membership exists for this user+org pair
        if organization:
            try:
                membership = Membership.objects.select_related(
                    "user", "organization"
                ).get(
                    user=request.user,
                    organization=organization,
                    is_active=True,
                )
            except Membership.DoesNotExist:
                # User has no valid membership for this org, clear it
                organization = None
                membership = None

        request.organization = organization
        request.membership = membership
