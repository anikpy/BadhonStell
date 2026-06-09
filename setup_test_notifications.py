#!/usr/bin/env python3
"""
Setup test data for notification system verification
"""
import os
import sys
import django
from datetime import date, timedelta
from random import randint

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
sys.path.insert(0, '/home/anik/Personal/BadhonStell')
django.setup()

from transactions.models import Customer, Transaction

def setup_test_payment_dates():
    """Set payment dates for existing transactions to test notifications"""
    print("=" * 60)
    print("SETTING UP TEST PAYMENT DATES")
    print("=" * 60)
    
    today = date.today()
    
    # Get all purchase transactions without payment_date
    purchases = Transaction.objects.filter(
        transaction_type='purchase',
        payment_date__isnull=True
    )
    
    print(f"\nFound {purchases.count()} purchase transactions without payment_date")
    
    if purchases.count() == 0:
        print("✅ All transactions already have payment_date set!")
        return
    
    updated_count = 0
    
    for txn in purchases:
        # Set payment date to various dates for testing
        # Some in the past (overdue), some today, some in future
        
        rand = randint(0, 10)
        
        if rand < 3:  # 30% - Today
            txn.payment_date = today
        elif rand < 6:  # 30% - Overdue (1-10 days ago)
            days_ago = randint(1, 10)
            txn.payment_date = today - timedelta(days=days_ago)
        elif rand < 9:  # 30% - Future (1-10 days from now)
            days_future = randint(1, 10)
            txn.payment_date = today + timedelta(days=days_future)
        else:  # 10% - Use delivery_date if available, otherwise today
            if txn.delivery_date:
                txn.payment_date = txn.delivery_date
            else:
                txn.payment_date = today
        
        txn.save()
        updated_count += 1
    
    print(f"✅ Updated {updated_count} transactions with payment dates")
    
    # Show summary
    print("\nSummary of payment dates:")
    print(f"  - TODAY ({today}): {Transaction.objects.filter(payment_date=today, transaction_type='purchase').count()}")
    print(f"  - OVERDUE: {Transaction.objects.filter(payment_date__lt=today, transaction_type='purchase').count()}")
    print(f"  - FUTURE: {Transaction.objects.filter(payment_date__gt=today, transaction_type='purchase').count()}")
    
    print("\n" + "=" * 60)
    print("✅ TEST DATA SETUP COMPLETE")
    print("=" * 60)
    print("\nNow run: python3 test_notifications.py")

if __name__ == '__main__':
    try:
        setup_test_payment_dates()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)