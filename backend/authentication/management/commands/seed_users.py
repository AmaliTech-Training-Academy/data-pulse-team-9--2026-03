"""Management command to seed default users from the project spec."""

from django.core.management.base import BaseCommand
from authentication.models import User


class Command(BaseCommand):
    help = "Seed default ADMIN and USER accounts per project specification."

    def handle(self, *args, **options):
        defaults = [
            {
                "email": "admin@amalitech.com",
                "password": "password123",
                "full_name": "Admin User",
                "role": "ADMIN",
            },
            {
                "email": "user@amalitech.com",
                "password": "password123",
                "full_name": "Regular User",
                "role": "USER",
            },
        ]

        for user_data in defaults:
            email = user_data["email"]
            if User.objects.filter(email=email).exists():
                self.stdout.write(self.style.WARNING(f"User {email} already exists, skipping."))
                continue

            if user_data["role"] == "ADMIN":
                User.objects.create_superuser(
                    email=email,
                    password=user_data["password"],
                    full_name=user_data["full_name"],
                )
            else:
                User.objects.create_user(
                    email=email,
                    password=user_data["password"],
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                )
            self.stdout.write(self.style.SUCCESS(f"Created {user_data['role']} user: {email}"))
