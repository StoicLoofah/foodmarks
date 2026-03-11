"""
Management command to create a dev superuser non-interactively.
Usage: python manage.py create_dev_user
Creates user 'admin' with password 'admin' if it doesn't already exist.
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a dev superuser (admin/admin) non-interactively"

    def handle(self, *args, **options):
        if User.objects.filter(username="admin").exists():
            self.stdout.write("Dev user 'admin' already exists.")
        else:
            User.objects.create_superuser(
                username="admin", email="admin@example.com", password="admin"
            )
            self.stdout.write(self.style.SUCCESS("Created superuser: admin / admin"))
