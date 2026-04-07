from django.conf import settings
from django.core.mail import send_mail


def send_invitation_email(invitation):
    """Send an invitation email with an accept link containing the token."""
    org_name = invitation.organization.name
    accept_url = f"{_get_base_url()}/invitations/{invitation.token}/accept/"

    subject = f"You've been invited to join {org_name} on TenantFlow"

    body = (
        f"Hello,\n\n"
        f"You've been invited to join {org_name} on TenantFlow "
        f"as a {invitation.get_role_display()}.\n\n"
        f"Click the link below to accept the invitation:\n"
        f"{accept_url}\n\n"
        f"This invitation will expire on "
        f"{invitation.expires_at.strftime('%B %d, %Y at %I:%M %p') if invitation.expires_at else 'N/A'}.\n\n"
        f"If you did not expect this invitation, you can safely ignore this email.\n\n"
        f"Best regards,\n"
        f"The TenantFlow Team"
    )

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invitation.email],
        fail_silently=False,
    )


def _get_base_url():
    """Return the base URL for the application."""
    return getattr(settings, "BASE_URL", "http://localhost:8000")
