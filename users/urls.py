from django.urls import path
from django.views.generic import RedirectView

from .views import AutoCreateLoginView, AutoCreateConfirmLoginCodeView


urlpatterns = [
    # Override main login view to auto-create users
    path(
        "login/",
        AutoCreateLoginView.as_view(),
        name="account_login",
    ),
    # Redirect /login/code/ to main login page to avoid bypassing auto-create logic
    path(
        "login/code/",
        RedirectView.as_view(pattern_name="account_login", permanent=True),
        name="account_request_login_code",
    ),
    path(
        "login/code/confirm/",
        AutoCreateConfirmLoginCodeView.as_view(),
        name="account_confirm_login_code",
    ),
    # Redirect signup to login since login auto-creates users
    path(
        "signup/",
        RedirectView.as_view(pattern_name="account_login", permanent=True),
        name="account_signup",
    ),
]
