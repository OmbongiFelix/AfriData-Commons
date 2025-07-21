from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Creates or updates a specific superuser regardless of others.'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not all([username, email, password]):
            self.stderr.write(self.style.ERROR("Missing superuser environment variables."))
            return

        user, created = User.objects.get_or_create(email=email, defaults={"username": username})

        # Update username if it changed
        if user.username != username:
            user.username = username

        # Ensure superuser and staff status
        user.is_superuser = True
        user.is_staff = True

        # Update password safely
        user.set_password(password)
        user.save()

        msg = "Superuser created." if created else "Superuser updated."
        self.stdout.write(self.style.SUCCESS(msg))
