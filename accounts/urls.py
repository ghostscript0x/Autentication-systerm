"""
URL configuration for the accounts app.

Maps URL patterns to views for registration, authentication,
email verification, password reset, and profile management.
"""

from django.urls import path
from django.contrib.auth import views as auth_views

from accounts import views

app_name = 'accounts'

urlpatterns = [
    # Registration
    path('register/', views.RegisterView.as_view(), name='register'),
    path(
        'verify-email-sent/',
        views.verify_email_sent,
        name='verify_email_sent',
    ),
    path(
        'activate/<uidb64>/<token>/',
        views.ActivateAccountView.as_view(),
        name='activate',
    ),

    # Login / Logout
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),

    # Password Reset
    path(
        'password-reset/',
        views.CustomPasswordResetView.as_view(),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        views.CustomPasswordResetDoneView.as_view(),
        name='password_reset_done',
    ),
    path(
        'password-reset-confirm/<uidb64>/<token>/',
        views.CustomPasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    path(
        'password-reset-complete/',
        views.CustomPasswordResetCompleteView.as_view(),
        name='password_reset_complete',
    ),

    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # Protected pages
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path(
        'account-settings/',
        views.AccountSettingsView.as_view(),
        name='account_settings',
    ),
]
