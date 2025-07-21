from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os
import environ

class Command(BaseCommand):
    help = 'Creates a superuser if none exist'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username=os.environ.get('DJANGO_SUPERUSER_USERNAME'),
                email=os.environ.get('DJANGO_SUPERUSER_EMAIL'),
                password=os.environ.get('DJANGO_SUPERUSER_PASSWORD')
            )
            self.stdout.write(self.style.SUCCESS('Superuser created.'))
        else:
            self.stdout.write('Superuser already exists.')


#Old Build command
#pip install -r ../requirements.txt && python manage.py migrate && python manage.py collectstatic --no-input

#New Build Command
#pip install -r ../requirements.txt && python manage.py migrate && python manage.py create_admin && python manage.py collectstatic --no-input


