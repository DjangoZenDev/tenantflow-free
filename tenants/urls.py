from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.tenant_dashboard, name="tenant_dashboard"),
    path("team/", views.team_members, name="team_members"),
    path("team/invite/", views.invite_member, name="invite_member"),
    path("usage/", views.usage_overview, name="usage_overview"),
    path("billing/", views.billing_view, name="billing_view"),
    path("settings/", views.organization_settings, name="organization_settings"),
    path("switch-org/", views.switch_organization, name="switch_organization"),
    path("invitations/<uuid:token>/accept/", views.accept_invitation, name="accept_invitation"),
    path("invitations/<int:pk>/resend/", views.resend_invitation, name="resend_invitation"),
    path("invitations/<int:pk>/revoke/", views.revoke_invitation, name="revoke_invitation"),
    path("upgrade/", views.upgrade_plan, name="upgrade_plan"),
    path("audit-log/", views.audit_log_view, name="audit_log"),
    path("global-settings/", views.global_settings_view, name="global_settings"),
    path("api/usage-chart/", views.usage_chart_data, name="usage_chart_data"),
]
