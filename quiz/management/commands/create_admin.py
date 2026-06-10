from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Creates a temporary deployment admin superuser accounts profile'

    def handle(self, *args, **options):
        # Choose your desired production username here
        username = 'admin' 
        email = 'admin@example.com'
        # Set a strong password here for your deployment login
        password = 'Test@1234' 

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' successfully deployed!"))
        else:
            self.stdout.write(self.style.WARNING(f"Superuser '{username}' already exists mapping."))
