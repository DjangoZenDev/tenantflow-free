"""
URL configuration for tenantflow project.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("tenants.api_urls")),
    path("", include("tenants.urls")),
]
