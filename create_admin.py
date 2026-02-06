#!/usr/bin/env python
"""
Admin User তৈরি করার স্ক্রিপ্ট
এই স্ক্রিপ্ট চালানোর জন্য: python create_admin.py
"""

import os
import django

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
django.setup()

from django.contrib.auth.models import User


def create_admin_user():
    """Admin user তৈরি করুন"""
    print("=" * 60)
    print("Admin User তৈরি করা হচ্ছে")
    print("=" * 60)
    
    username = 'admin'
    email = 'admin@badhonsteel.com'
    password = 'admin1234'
    
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        print(f"\n⚠️  '{username}' ইউজার ইতিমধ্যে আছে!")
        
        response = input("\nপুরাতন ইউজার মুছে নতুন তৈরি করবেন? (y/n): ")
        if response.lower() == 'y':
            User.objects.filter(username=username).delete()
            print("✓ পুরাতন ইউজার মুছে ফেলা হয়েছে")
        else:
            print("\n✅ বিদ্যমান ইউজার ব্যবহার করুন:")
            print(f"   Username: {username}")
            print(f"   Password: (আপনার সেট করা পাসওয়ার্ড)")
            return
    
    # Create superuser
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    
    print("\n✅ Admin user সফলভাবে তৈরি হয়েছে!")
    print("\n📝 লগইন তথ্য:")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
    print(f"   Email: {email}")
    
    print("\n🔐 লগইন করুন:")
    print("   অ্যাডমিন প্যানেল: http://127.0.0.1:8000/admin-panel/login/")
    print("   Django Admin: http://127.0.0.1:8000/django-admin/")
    
    print("\n⚠️  নিরাপত্তা সতর্কতা:")
    print("   Production এ deploy করার আগে পাসওয়ার্ড পরিবর্তন করুন!")
    print("   Django Admin থেকে পাসওয়ার্ড পরিবর্তন করতে পারবেন।")


if __name__ == '__main__':
    try:
        create_admin_user()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

