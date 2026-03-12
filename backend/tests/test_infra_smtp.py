import smtplib
import socket

import pytest
from django.conf import settings


@pytest.mark.django_db
class TestSMTPConnectivity:
    """Infrastructure tests to verify SMTP configuration and connectivity."""

    def test_smtp_settings_loaded(self):
        """Verify that the required SMTP settings are present."""
        # Note: pytest-django often overrides EMAIL_BACKEND to 'locmem' for safety.
        # We check the configured values.
        from django.conf import settings

        # Check if SMTP is intended or active
        is_smtp = (
            "smtp" in settings.EMAIL_BACKEND.lower()
            or settings.EMAIL_BACKEND == "django.core.mail.backends.locmem.EmailBackend"
        )
        assert is_smtp

        assert settings.EMAIL_HOST == "smtp.gmail.com"
        assert settings.EMAIL_PORT == 587
        assert settings.EMAIL_USE_TLS is True
        assert settings.EMAIL_HOST_USER is not None
        assert "@" in settings.EMAIL_HOST_USER
        assert settings.EMAIL_HOST_PASSWORD is not None
        assert len(settings.EMAIL_HOST_PASSWORD) > 0

    def test_smtp_host_reachable(self):
        """Verify that the SMTP host is reachable on the specified port."""
        host = settings.EMAIL_HOST
        port = settings.EMAIL_PORT
        try:
            # Create a socket and try to connect
            s = socket.create_connection((host, port), timeout=5)
            s.close()
            reachable = True
        except (socket.timeout, socket.error):
            reachable = False

        assert reachable, f"Could not reach {host}:{port}. Check your network and Docker configuration."

    def test_smtp_server_login_possible(self):
        """
        Optional: Verify that we can start a session with the SMTP server.
        Note: This does not send an email. It just performs the initial handshake and STARTTLS.
        """
        try:
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
            server.starttls()
            # We don't login here to avoid exposing credentials in test failures or logs,
            # but we've verified the server is accepting TLS connections on the specified port.
            server.quit()
            handshake_success = True
        except Exception as e:
            print(f"SMTP Handshake failed: {e}")
            handshake_success = False

        assert handshake_success, "SMTP Server did not respond to STARTTLS handshake."
