# Standard Library
import os

# Django
import django
from django.core.management import call_command

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testauth.settings.local")
django.setup()
call_command("makemigrations", "industry_reforged")
