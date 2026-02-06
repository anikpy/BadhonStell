#!/usr/bin/env python
"""
Sample Data তৈরি করার স্ক্রিপ্ট
এই স্ক্রিপ্ট চালানোর জন্য: python create_sample_data.py
"""

import os
import django
from datetime import date, timedelta

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
django.setup()

from shop.models import ShopInfo, Product, Order


def create_shop_info():
    """দোকানের তথ্য তৈরি করুন"""
    print("📝 দোকানের তথ্য তৈরি করা হচ্ছে...")
    
    # পুরাতন ডাটা মুছে ফেলুন (যদি থাকে)
    ShopInfo.objects.all().delete()
    
    shop = ShopInfo.objects.create(
        name='বাধন স্টিল',
        description='স্টিল ও লোহার সকল ধরনের কাজ করা হয়। দরজা, জানালা, গ্রিল, গেট, রেলিং, শেড ইত্যাদি তৈরি করি। উচ্চমানের কাজ এবং সাশ্রয়ী মূল্যে।',
        phone='01712345678',
        whatsapp='01712345678',
        address='মিরপুর, ঢাকা-১২১৬, বাংলাদেশ'
    )
    print(f"✅ দোকানের তথ্য তৈরি হয়েছে: {shop.name}")
    return shop


def create_products():
    """নমুনা পণ্য তৈরি করুন"""
    print("\n📦 নমুনা পণ্য তৈরি করা হচ্ছে...")
    
    # পুরাতন পণ্য মুছে ফেলুন (যদি থাকে)
    Product.objects.all().delete()
    
    products_data = [
        {
            'name': 'স্টিল দরজা (স্ট্যান্ডার্ড)',
            'category': 'door',
            'description': '৭ ফুট x ৪ ফুট স্ট্যান্ডার্ড স্টিল দরজা। টেকসই এবং নিরাপদ। বিভিন্ন ডিজাইন এবং রঙে পাওয়া যায়।',
            'estimated_price': 15000.00
        },
        {
            'name': 'স্টিল দরজা (প্রিমিয়াম)',
            'category': 'door',
            'description': '৮ ফুট x ৪.৫ ফুট প্রিমিয়াম স্টিল দরজা। অতিরিক্ত নিরাপত্তা সহ। আধুনিক ডিজাইন।',
            'estimated_price': 25000.00
        },
        {
            'name': 'স্টিল জানালা',
            'category': 'window',
            'description': '৪ ফুট x ৩ ফুট স্টিল জানালা। গ্রিল সহ। বিভিন্ন ডিজাইনে পাওয়া যায়।',
            'estimated_price': 8000.00
        },
        {
            'name': 'উইন্ডো গ্রিল',
            'category': 'grill',
            'description': 'কাস্টম সাইজের উইন্ডো গ্রিল। নিরাপত্তা এবং সৌন্দর্য দুটোই নিশ্চিত করে।',
            'estimated_price': 5000.00
        },
        {
            'name': 'মেইন গেট',
            'category': 'gate',
            'description': '১২ ফুট x ৮ ফুট মেইন গেট। অটোমেটিক সিস্টেম যুক্ত করা যায়। আকর্ষণীয় ডিজাইন।',
            'estimated_price': 45000.00
        },
        {
            'name': 'সিঁড়ির রেলিং',
            'category': 'railing',
            'description': 'স্টেইনলেস স্টিল রেলিং। প্রতি ফুট হিসাবে। আধুনিক এবং টেকসই।',
            'estimated_price': 1200.00
        },
        {
            'name': 'বারান্দার রেলিং',
            'category': 'railing',
            'description': 'বারান্দার জন্য ডিজাইনার রেলিং। নিরাপদ এবং সুন্দর।',
            'estimated_price': 18000.00
        },
        {
            'name': 'গ্যারেজ শেড',
            'category': 'shed',
            'description': '১০ ফুট x ১২ ফুট গ্যারেজ শেড। টিন এবং স্টিল ফ্রেম সহ।',
            'estimated_price': 35000.00
        },
    ]
    
    created_products = []
    for product_data in products_data:
        product = Product.objects.create(**product_data)
        created_products.append(product)
        print(f"  ✓ {product.name} - ৳{product.estimated_price}")
    
    print(f"✅ মোট {len(created_products)} টি পণ্য তৈরি হয়েছে")
    return created_products


def create_orders():
    """নমুনা অর্ডার তৈরি করুন"""
    print("\n📋 নমুনা অর্ডার তৈরি করা হচ্ছে...")
    
    # পুরাতন অর্ডার মুছে ফেলুন (যদি থাকে)
    Order.objects.all().delete()
    
    today = date.today()
    
    orders_data = [
        {
            'customer_name': 'মোঃ রহিম উদ্দিন',
            'mobile_number': '01712345678',
            'product_name': 'স্টিল দরজা (স্ট্যান্ডার্ড)',
            'product_description': '৭ ফুট x ৪ ফুট, সাদা রঙের, সাধারণ ডিজাইন',
            'total_price': 15000.00,
            'cash_paid': 10000.00,
            'order_date': today - timedelta(days=5),
            'delivery_date': today + timedelta(days=10),
            'status': 'pending'
        },
        {
            'customer_name': 'সালমা বেগম',
            'mobile_number': '01823456789',
            'product_name': 'উইন্ডো গ্রিল',
            'product_description': '৪ ফুট x ৩ ফুট, ২টি জানালার জন্য',
            'total_price': 10000.00,
            'cash_paid': 10000.00,
            'order_date': today - timedelta(days=15),
            'delivery_date': today - timedelta(days=5),
            'status': 'completed'
        },
        {
            'customer_name': 'আব্দুল করিম',
            'mobile_number': '01934567890',
            'product_name': 'মেইন গেট',
            'product_description': '১২ ফুট x ৮ ফুট, কালো রঙের, ডিজাইনার প্যাটার্ন',
            'total_price': 50000.00,
            'cash_paid': 25000.00,
            'order_date': today - timedelta(days=3),
            'delivery_date': today + timedelta(days=20),
            'status': 'pending'
        },
        {
            'customer_name': 'ফাতেমা খাতুন',
            'mobile_number': '01645678901',
            'product_name': 'সিঁড়ির রেলিং',
            'product_description': '২৫ ফুট, স্টেইনলেস স্টিল',
            'total_price': 30000.00,
            'cash_paid': 15000.00,
            'order_date': today - timedelta(days=7),
            'delivery_date': today + timedelta(days=8),
            'status': 'pending'
        },
    ]
    
    created_orders = []
    for order_data in orders_data:
        order = Order.objects.create(**order_data)
        created_orders.append(order)
        status_emoji = '⏳' if order.status == 'pending' else '✅'
        print(f"  {status_emoji} {order.customer_name} - {order.product_name} - ৳{order.total_price}")
    
    print(f"✅ মোট {len(created_orders)} টি অর্ডার তৈরি হয়েছে")
    return created_orders


def main():
    """মূল ফাংশন"""
    print("=" * 60)
    print("বাধন স্টিল - Sample Data তৈরি করা হচ্ছে")
    print("=" * 60)
    
    try:
        shop = create_shop_info()
        products = create_products()
        orders = create_orders()
        
        print("\n" + "=" * 60)
        print("✅ সফলভাবে সম্পন্ন হয়েছে!")
        print("=" * 60)
        print(f"\n📊 সারসংক্ষেপ:")
        print(f"  • দোকান: {shop.name}")
        print(f"  • পণ্য: {len(products)} টি")
        print(f"  • অর্ডার: {len(orders)} টি")
        print(f"    - চলমান: {Order.objects.filter(status='pending').count()} টি")
        print(f"    - সম্পন্ন: {Order.objects.filter(status='completed').count()} টি")
        
        print("\n🚀 এখন সার্ভার চালু করুন:")
        print("   python manage.py runserver")
        print("\n🌐 ব্রাউজারে খুলুন:")
        print("   http://127.0.0.1:8000/")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

