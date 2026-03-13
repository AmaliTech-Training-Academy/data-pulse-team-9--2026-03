import smtplib
import socket

import pytest
from django.conf import settings


@pytest.mark.django_db
class TestSMTPConnectivity:
    """Infrastructure tests to verify SMTP configuration and connectivity."""

    def test_smtp_settings_loaded(self):
        """Verify that the required SMTP settings are present."""
        from django.conf import settings

        # Check if SMTP is intended or active
        is_smtp = (
            "smtp" in settings.EMAIL_BACKEND.lower()
            or settings.EMAIL_BACKEND == "django.core.mail.backends.locmem.EmailBackend"
            or settings.EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend"
        )
        assert is_smtp

        # Verify that settings are present. We don't hardcode "smtp.gmail.com"
        # because CI uses different defaults (localhost).
        assert settings.EMAIL_HOST is not None
        assert settings.EMAIL_PORT is not None
        assert len(str(settings.EMAIL_HOST)) > 0

    def test_smtp_host_reachable(self):
        """Verify that the SMTP host is reachable on the specified port."""
        host = settings.EMAIL_HOST
        port = settings.EMAIL_PORT

        # Skip if using common development defaults in CI/Local
        if host in ["localhost", "127.0.0.1"] and port == 1025:
            pytest.skip("Skipping connectivity test for default localhost:1025 settings.")

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
        if settings.EMAIL_HOST in ["localhost", "127.0.0.1"] and settings.EMAIL_PORT == 1025:
            pytest.skip("Skipping SMTP handshake for default localhost:1025 settings.")

        try:
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
            if settings.EMAIL_USE_TLS:
                server.starttls()
            # We don't login here to avoid exposing credentials in test failures or logs,
            # but we've verified the server is accepting TLS connections on the specified port.
            server.quit()
            handshake_success = True
        except Exception as e:
            print(f"SMTP Handshake failed: {e}")
            handshake_success = False

        assert handshake_success, "SMTP Server did not respond to handshake."
