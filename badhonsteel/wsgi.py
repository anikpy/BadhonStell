"""
WSGI config for badhonsteel project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')

application = get_wsgi_application()

