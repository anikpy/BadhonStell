#!/usr/bin/env python3
"""
Verify that templates are properly configured in transactions app
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.template.loader import get_template
from django.conf import settings

print("=" * 60)
print("TEMPLATE VERIFICATION")
print("=" * 60)

# Check template directories
print("\n1. Template DIRS configuration:")
for dir_path in settings.TEMPLATES[0]['DIRS']:
    print(f"   📁 {dir_path}")
    print(f"   Exists: {os.path.exists(dir_path)}")

# Check APP_DIRS setting
print(f"\n2. APP_DIRS setting: {settings.TEMPLATES[0]['APP_DIRS']}")

# List all template directories Django will search
print("\n3. Template search paths:")
from django.template.utils import get_app_template_dirs
for template_dir in get_app_template_dirs('html'):
    print(f"   📁 {template_dir}")

# Try to load a template
print("\n4. Testing template loading:")
templates_to_test = [
    'transactions/customer_list.html',
    'transactions/customer_detail.html',
    'transactions/transaction_purchase_form.html',
    'transactions/order_create.html',
]

for template_name in templates_to_test:
    try:
        template = get_template(template_name)
        print(f"   ✅ {template_name}")
        print(f"      Template object: {template}")
    except Exception as e:
        print(f"   ❌ {template_name}")
        print(f"      Error: {str(e)}")

# Check if template files exist on disk
print("\n5. Checking template files on disk:")
template_dir = os.path.join(os.path.dirname(__file__), 'transactions', 'templates', 'transactions')
print(f"   Looking in: {template_dir}")
print(f"   Directory exists: {os.path.exists(template_dir)}")

if os.path.exists(template_dir):
    templates = os.listdir(template_dir)
    print(f"   Found {len(templates)} templates:")
    for template in sorted(templates):
        print(f"      - {template}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)