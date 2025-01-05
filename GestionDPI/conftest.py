import os
import django
from django.conf import settings

# This is needed for Django to find your settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GestionDPI.settings')
django.setup()