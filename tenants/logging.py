from .models import ActivityLog, AuditLog


def log_activity(request, action, detail="", target_type="", target_id=None):
    """Create an ActivityLog entry for the current organization."""
    org = getattr(request, "organization", None)
    if not org:
        return None

    return ActivityLog.objects.create(
        organization=org,
        user=request.user if request.user.is_authenticated else None,
        action=action,
        detail=detail,
        target_type=target_type,
        target_id=target_id,
    )


def log_audit(request, action, instance, changes=None):
    """Create an AuditLog entry with IP extraction and model info."""
    org = getattr(request, "organization", None)
    if not org:
        return None

    # Extract client IP address
    ip_address = _get_client_ip(request)

    return AuditLog.objects.create(
        organization=org,
        user=request.user if request.user.is_authenticated else None,
        action=action,
        target_model=instance.__class__.__name__,
        target_id=instance.pk,
        changes=changes or {},
        ip_address=ip_address,
    )


def _get_client_ip(request):
    """Extract the client IP address from the request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
