import os

import django
from django.conf import settings
from django.core.mail import send_mail

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datapulse.settings.dev")
django.setup()


def test_send_email():
    print("--- Starting SMTP Direct Test ---")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

    subject = "SMTP Direct Test - DataPulse"
    message = "If you are reading this, SMTP is working correctly in the DataPulse backend."
    recipient_list = [settings.DEFAULT_FROM_EMAIL]

    try:
        sent = send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
        if sent:
            print(f"\nSUCCESS: Email sent to {recipient_list}")
        else:
            print("\nFAILURE: Email not sent.")
    except Exception as e:
        print(f"\nERROR: {str(e)}")

    print("-------------------------------------------------------------------------------")


# Explicitly call the function for use with manage.py shell
test_send_email()
