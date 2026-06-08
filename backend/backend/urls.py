"""
URL configuration for the backend project.

Defines the top‑level URL patterns that include Django admin, the API
endpoints, and authentication endpoints for JWT tokens.  Additional app
urlconfs (such as `core.urls`) are included via `include()`.
"""
from __future__ import annotations

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    # JWT endpoints provided by djangorestframework-simplejwt
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
