from django import forms
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from wagtail.users.forms import UserEditForm, UserCreationForm
from wagtail.images.widgets import AdminImageChooser
from wagtail.images import get_image_model

from allauth.account import app_settings as account_settings
from allauth.account.adapter import get_adapter
from allauth.account.forms import LoginForm, RequestLoginCodeForm, ConfirmLoginCodeForm
from allauth.account.utils import filter_users_by_email
from allauth.core import ratelimit

from .models import User


class RememberMeLoginForm(LoginForm):
    """Custom LoginForm that preserves 'remember me' for code-based login.

    allauth's default LoginForm handles session expiry for password login,
    but not for code-based login. This form stores the remember preference
    in the session so it can be applied after code verification.
    """

    def _login_by_code(self, request, redirect_url, credentials):
        # Store remember preference in session before code flow
        remember = account_settings.SESSION_REMEMBER
        if remember is None:
            remember = self.cleaned_data.get("remember", False)
        request.session["account_login_remember"] = remember

        return super()._login_by_code(request, redirect_url, credentials)


class AutoCreateRequestLoginCodeForm(RequestLoginCodeForm):
    """
    Custom login code request form that auto-creates users if they don't exist.

    New users are created as inactive (is_active=False) and will be activated
    upon successful code verification.
    """

    def clean_email(self):
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("AutoCreateRequestLoginCodeForm.clean_email called!")
        print("DEBUG: AutoCreateRequestLoginCodeForm.clean_email called!")

        email = self.cleaned_data.get("email")
        if not email:
            raise forms.ValidationError(_("Email is required."))

        adapter = get_adapter()
        email = adapter.clean_email(email)

        # Look for existing active users
        users = filter_users_by_email(email, is_active=True, prefer_verified=True)

        if users:
            # Existing active user - use them
            self._user = users[0]
        else:
            # Check for inactive user (pending verification from previous attempt)
            inactive_user = User.objects.filter(email__iexact=email, is_active=False).first()
            if inactive_user:
                self._user = inactive_user
            else:
                # Create new inactive user
                try:
                    self._user = User.objects.create_user(email=email, password=None)
                    self._user.is_active = False
                    self._user.save(update_fields=['is_active'])
                except IntegrityError:
                    # Race condition - user was created by another request
                    users = filter_users_by_email(email, is_active=True, prefer_verified=True)
                    if users:
                        self._user = users[0]
                    else:
                        inactive_user = User.objects.filter(email__iexact=email, is_active=False).first()
                        if inactive_user:
                            self._user = inactive_user
                        else:
                            raise forms.ValidationError(_("An error occurred. Please try again."))

        # Apply rate limiting
        if not ratelimit.consume(
            self.request,
            action="request_login_code",
            key=email.lower(),
        ):
            raise forms.ValidationError(_("Too many login attempts. Please try again later."))

        return email


class AutoCreateConfirmLoginCodeForm(ConfirmLoginCodeForm):
    """
    Custom login code confirmation form that activates users upon successful verification.
    """

    def login(self, request, redirect_url=None):
        # Activate user if they were inactive (new user)
        if self.user and not self.user.is_active:
            self.user.is_active = True
            self.user.save(update_fields=['is_active'])

        return super().login(request, redirect_url)


class CustomUserEditForm(UserEditForm):
    phone = forms.CharField(max_length=30, required=True, label=_("Phone"))
    profile_pic = forms.ModelChoiceField(
        queryset=get_image_model().objects.all(),
        widget=AdminImageChooser(),
        label=_('Profile Picture'),
    )


class CustomUserCreationForm(UserCreationForm):
    phone = forms.CharField(max_length=30, required=True, label=_("Phone"))
    profile_pic = forms.ModelChoiceField(
        queryset=get_image_model().objects.all(),
        widget=AdminImageChooser(),
        label=_('Profile Picture'),
    )
