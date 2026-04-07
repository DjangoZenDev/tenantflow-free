# TenantFlow Free

**SaaS Multi-Tenant Dashboard — Free Edition**
*By DjangoZen - https://djangozen.com*

This is the **free version** of TenantFlow. It includes core functionality to help you evaluate the product.

## Free Features
- Tenant dashboard with metrics overview
- Team member list with roles
- Usage progress bars
- Login and authentication

## Pro Features (Upgrade Required)
- Tenant branding (custom colors, logo per organization)
- Audit log with full action tracking
- Subscription billing flow with plan upgrades
- Team invitations with email delivery
- Organization switching for multi-org users
- Granular role-based permissions (owner, admin, member, viewer)
- Live activity feed

**Upgrade to TenantFlow Pro:** https://djangozen.com/product/tenantflow-pro/

## Quick Start

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations and seed data:
```bash
python manage.py migrate
python manage.py seed_data
```

4. Start server:
```bash
python manage.py runserver
```

5. Login: **admin** / **admin123**

---
*Free version by DjangoZen. Upgrade to Pro at https://djangozen.com/product/tenantflow-pro/*
*Copyright 2026 DjangoZen. All Rights Reserved.*
