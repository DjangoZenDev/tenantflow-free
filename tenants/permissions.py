from functools import wraps

from django.shortcuts import render

from .models import ROLE_HIERARCHY


def require_role(*allowed_roles):
    """Decorator that checks user has one of the allowed roles in current org."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            membership = getattr(request, "membership", None)
            if not membership or membership.role not in allowed_roles:
                return render(request, "tenants/permission_denied.html", {
                    "required_roles": [r for r in allowed_roles],
                    "current_role": membership.role if membership else "none",
                }, status=403)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def has_min_role(membership, min_role):
    """Check if a membership has at least the given minimum role level."""
    if not membership:
        return False
    return ROLE_HIERARCHY.get(membership.role, 0) >= ROLE_HIERARCHY.get(min_role, 0)
