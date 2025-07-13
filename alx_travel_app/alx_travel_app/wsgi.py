"""
WSGI config for alx_travel_app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import dotenv
from django.core.wsgi import get_wsgi_application

dotenv.load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.settings')

application = get_wsgi_application()
