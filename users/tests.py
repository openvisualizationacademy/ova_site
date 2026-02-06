import pytest
from django.urls import reverse

from users.models import User


@pytest.mark.django_db
class TestLoginRedirects:
    """Test that legacy URLs redirect to the main login page."""

    def test_login_code_url_redirects_to_login(self, client):
        """Accessing /accounts/login/code/ should redirect to /accounts/login/."""
        response = client.get("/accounts/login/code/")
        assert response.status_code == 301
        assert response.url == reverse("account_login")

    def test_login_code_url_redirects_with_next_param(self, client):
        """Redirect should be permanent (301) even with query params."""
        response = client.get("/accounts/login/code/?next=/courses/")
        assert response.status_code == 301

    def test_signup_redirects_to_login(self, client):
        """Accessing /accounts/signup/ should redirect to /accounts/login/."""
        response = client.get("/accounts/signup/")
        assert response.status_code == 301
        assert response.url == reverse("account_login")


@pytest.mark.django_db
class TestAutoCreateLogin:
    """Test that users are auto-created when they attempt to login."""

    def test_login_creates_new_user(self, client):
        """Submitting login form with new email should create a user."""
        email = "newuser@example.com"
        assert not User.objects.filter(email=email).exists()

        response = client.post(
            reverse("account_login"),
            {"login": email},
        )

        # User should be created
        assert User.objects.filter(email=email).exists()
        user = User.objects.get(email=email)
        assert user.is_active is True

        # Should redirect to code confirmation page
        assert response.status_code == 302
        assert "login/code/confirm" in response.url

    def test_login_existing_user_no_duplicate(self, client):
        """Submitting login form with existing email should not create duplicate."""
        email = "existing@example.com"
        User.objects.create_user(email=email, password=None)
        assert User.objects.filter(email=email).count() == 1

        response = client.post(
            reverse("account_login"),
            {"login": email},
        )

        # Should still be only one user
        assert User.objects.filter(email=email).count() == 1

        # Should redirect to code confirmation page
        assert response.status_code == 302
        assert "login/code/confirm" in response.url

    def test_login_case_insensitive_email(self, client):
        """Email lookup should be case-insensitive."""
        email = "TestUser@Example.com"
        User.objects.create_user(email=email.lower(), password=None)

        response = client.post(
            reverse("account_login"),
            {"login": email.upper()},
        )

        # Should not create a new user
        assert User.objects.filter(email__iexact=email).count() == 1

        # Should redirect to code confirmation page
        assert response.status_code == 302

    def test_login_normalizes_email_case(self, client):
        """Login should normalize email to lowercase."""
        # Create user with mixed case email - should be stored lowercase
        mixed_case_email = "John.Doe@Example.COM"
        user = User.objects.create_user(email=mixed_case_email, password=None)
        assert user.email == mixed_case_email.lower()

        # Login with different casing should still work
        response = client.post(
            reverse("account_login"),
            {"login": "JOHN.DOE@EXAMPLE.COM"},
        )

        # Should redirect to code confirmation page
        assert response.status_code == 302
        assert "login/code/confirm" in response.url

        # Should not create a duplicate user
        assert User.objects.filter(email__iexact=mixed_case_email).count() == 1

    def test_login_post_does_not_500(self, client):
        """Login POST should not return a server error."""
        response = client.post(
            reverse("account_login"),
            {"login": "test500@example.com"},
        )
        # Should redirect to confirm page, not error
        assert response.status_code != 500
        assert response.status_code == 302

    def test_login_activates_inactive_user(self, client):
        """Login should activate an inactive user."""
        email = "inactive@example.com"
        user = User.objects.create_user(email=email, password=None)
        user.is_active = False
        user.save(update_fields=['is_active'])

        assert User.objects.get(email=email).is_active is False

        response = client.post(
            reverse("account_login"),
            {"login": email},
        )

        # User should now be active
        user.refresh_from_db()
        assert user.is_active is True

        # Should redirect to code confirmation page
        assert response.status_code == 302
        assert "login/code/confirm" in response.url

    def test_login_fixes_existing_user_email_case(self, client):
        """Login should normalize existing user's email to lowercase."""
        # Simulate a user created before the lowercase fix
        mixed_case_email = "Legacy.User@Example.COM"
        user = User(email=mixed_case_email, is_active=True)
        user.set_unusable_password()
        user.save()

        assert user.email == mixed_case_email  # Not normalized yet

        response = client.post(
            reverse("account_login"),
            {"login": mixed_case_email},
        )

        # Email should now be normalized to lowercase
        user.refresh_from_db()
        assert user.email == mixed_case_email.lower()

        # Should redirect to code confirmation page
        assert response.status_code == 302
        assert "login/code/confirm" in response.url


@pytest.mark.django_db
class TestLoginCodeConfirm:
    """Test the login code confirmation page."""

    def test_confirm_page_without_session_redirects(self, client):
        """Accessing confirm page without a pending login should redirect."""
        response = client.get(reverse("account_confirm_login_code"))
        # Should redirect back to login since there's no pending code
        assert response.status_code == 302
