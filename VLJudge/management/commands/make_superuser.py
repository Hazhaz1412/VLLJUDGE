from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Make a user a superuser'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        try:
            user = User.objects.get(username=username)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'User "{username}" has been made a superuser.'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" does not exist.'))
