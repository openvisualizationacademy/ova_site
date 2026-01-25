from django.urls import path

from .views import AutoCreateLoginView, AutoCreateRequestLoginCodeView, AutoCreateConfirmLoginCodeView


urlpatterns = [
    # Override main login view to auto-create users
    path(
        "login/",
        AutoCreateLoginView.as_view(),
        name="account_login",
    ),
    path(
        "login/code/",
        AutoCreateRequestLoginCodeView.as_view(),
        name="account_request_login_code",
    ),
    path(
        "login/code/confirm/",
        AutoCreateConfirmLoginCodeView.as_view(),
        name="account_confirm_login_code",
    ),
]
