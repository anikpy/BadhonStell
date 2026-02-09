# Script to create/update admin user and fetch a protected page using Django test client
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client

USERNAME = 'admin'
PASSWORD = 'admin1234'
EMAIL = 'admin@badhonsteel.com'

u, created = User.objects.get_or_create(username=USERNAME, defaults={'email': EMAIL, 'is_staff': True, 'is_superuser': True})
if not created:
    u.email = EMAIL
    u.is_staff = True
    u.is_superuser = True
    u.set_password(PASSWORD)
    u.save()
else:
    u.set_password(PASSWORD)
    u.save()

print(f"Superuser ensured: {USERNAME}")

c = Client()
logged_in = c.login(username=USERNAME, password=PASSWORD)
print('Logged in:', logged_in)

# Change the URL here to test different admin pages
url = '/admin-panel/invoices/create/'
resp = c.get(url)
print('Requested:', url)
print('Status code:', resp.status_code)
try:
    print('Redirect chain:', resp.redirect_chain)
except Exception as e:
    print('Redirect chain not available:', type(e).__name__, str(e))

try:
    content = resp.content.decode('utf-8')
    summary = content[:3000]
    print('Page content preview (first 3000 chars):')
    print(summary)
except Exception as e:
    print('Could not decode response content:', type(e).__name__, str(e))

# Helper: check for Django debug tracebacks
try:
    if 'Traceback' in resp.content.decode('utf-8'):
        print('\nFound Traceback in response:')
        start = resp.content.decode('utf-8').find('Traceback')
        print(resp.content.decode('utf-8')[start:start+2000])
except Exception:
    pass
