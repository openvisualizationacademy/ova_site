import logging

from allauth.account import app_settings as account_settings
from allauth.account.views import LoginView, ConfirmLoginCodeView

from .forms import AutoCreateConfirmLoginCodeForm, RememberMeLoginForm
from .models import User

logger = logging.getLogger(__name__)


class AutoCreateLoginView(LoginView):
    """
    Custom login view that auto-creates users when ACCOUNT_LOGIN_BY_CODE_REQUIRED is True.

    When a user submits their email, if the user doesn't exist, we create them
    as inactive before the form is validated, so allauth sees them as existing.

    Also uses RememberMeLoginForm to preserve 'remember me' for code-based login.
    """
    form_class = RememberMeLoginForm

    def post(self, request, *args, **kwargs):
        """Create user before form validation so allauth finds them."""
        # Get email from POST data before form processing
        email = request.POST.get('login') or request.POST.get('email')
        logger.warning(f"DEBUG: AutoCreateLoginView.post() - email from POST: {email}")

        if email:
            self._ensure_user_exists(email)

        return super().post(request, *args, **kwargs)

    def _ensure_user_exists(self, email):
        """Create an active user if they don't exist, or activate if inactive.

        We create/activate users as active because:
        1. allauth's filter_users_by_email only finds active users
        2. The OTP code verification serves as the email verification
        3. If someone requests a code but never uses it, the cleanup task will remove them

        Email is normalized to lowercase to ensure allauth can find the user.
        """
        from allauth.account.utils import filter_users_by_email

        # Normalize email to lowercase for consistent lookups
        email = email.lower()

        # Check if user exists (active)
        users = filter_users_by_email(email, is_active=True, prefer_verified=True)
        if users:
            logger.debug(f"Found existing active user {users[0].pk}")
            return

        # Check for existing user (case-insensitive) and normalize/activate them
        existing = User.objects.filter(email__iexact=email).first()
        if existing:
            update_fields = []
            if not existing.is_active:
                existing.is_active = True
                update_fields.append('is_active')
                logger.debug(f"Activating inactive user {existing.pk}")
            # Normalize email to lowercase if needed
            if existing.email != email:
                existing.email = email
                update_fields.append('email')
                logger.debug(f"Normalizing email case for user {existing.pk}")
            if update_fields:
                existing.save(update_fields=update_fields)
            return

        # Create new active user with lowercase email
        logger.debug(f"Creating new user for {email}")
        try:
            user = User.objects.create_user(email=email, password=None)
            logger.debug(f"Created user {user.pk} (is_active={user.is_active})")
        except Exception as e:
            logger.warning(f"Error creating user: {e}")


class AutoCreateConfirmLoginCodeView(ConfirmLoginCodeView):
    """Custom view that applies 'remember me' after code verification."""
    form_class = AutoCreateConfirmLoginCodeForm

    def form_valid(self, form):
        response = super().form_valid(form)

        # Apply remember me preference from initial login form
        remember = self.request.session.pop("account_login_remember", None)
        if remember is None:
            remember = account_settings.SESSION_REMEMBER

        if remember:
            self.request.session.set_expiry(account_settings.SESSION_COOKIE_AGE)
        elif remember is False:
            self.request.session.set_expiry(0)
        # If remember is still None (no setting, no checkbox), use Django's default

        return response
