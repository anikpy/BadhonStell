#!/usr/bin/env python3
"""
Test script to verify notification system is working
"""
import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
sys.path.insert(0, '/home/anik/Personal/BadhonStell')
django.setup()

from transactions.models import Customer, Transaction, Notification
from transactions.notifications import generate_payment_notifications, get_unread_notification_count

def test_notification_system():
    """Test the notification system"""
    print("=" * 60)
    print("NOTIFICATION SYSTEM VERIFICATION")
    print("=" * 60)
    
    # Check if we have any customers
    customers = Customer.objects.all()
    print(f"\n1. Total Customers: {customers.count()}")
    
    if customers.count() == 0:
        print("   ⚠️ No customers found. Please create a customer first.")
        return False
    
    # Check if we have any purchase transactions
    purchases = Transaction.objects.filter(transaction_type='purchase')
    print(f"2. Total Purchase Transactions: {purchases.count()}")
    
    if purchases.count() == 0:
        print("   ⚠️ No purchase transactions found. Please create a purchase order first.")
        return False
    
    # Check transactions with payment_date
    with_payment_date = purchases.filter(payment_date__isnull=False)
    print(f"3. Purchases with Payment Date: {with_payment_date.count()}")
    
    if with_payment_date.count() == 0:
        print("   ⚠️ No transactions have payment_date set.")
        print("   💡 TIP: Edit a purchase transaction and add a payment date.")
        return False
    
    # Show some sample transactions with payment dates
    print("\n4. Sample Transactions with Payment Dates:")
    for txn in with_payment_date[:5]:
        days_diff = (date.today() - txn.payment_date).days if txn.payment_date else None
        status = ""
        if days_diff is not None:
            if days_diff < 0:
                status = f"Due in {abs(days_diff)} days"
            elif days_diff == 0:
                status = "DUE TODAY"
            else:
                status = f"OVERDUE by {days_diff} days"
        
        print(f"   - {txn.transaction_number}: {txn.customer.name} | Payment: {txn.payment_date} | {status}")
    
    # Generate notifications
    print("\n5. Generating Notifications...")
    created_count = generate_payment_notifications()
    print(f"   ✅ Created {created_count} new notifications")
    
    # Check total notifications
    total_notifications = Notification.objects.count()
    unread_count = get_unread_notification_count()
    print(f"\n6. Notification Statistics:")
    print(f"   - Total Notifications: {total_notifications}")
    print(f"   - Unread Notifications: {unread_count}")
    
    # Show recent notifications
    print("\n7. Recent Notifications:")
    recent_notifications = Notification.objects.all().order_by('-created_at')[:10]
    for notif in recent_notifications:
        status = "✓ Read" if notif.is_read else "🔴 Unread"
        print(f"   - [{notif.notification_type}] {notif.title}")
        print(f"     Customer: {notif.customer.name} | {status}")
        print(f"     Created: {notif.created_at.strftime('%Y-%m-%d %H:%M')}")
        if notif.transaction:
            print(f"     Transaction: {notif.transaction.transaction_number}")
        print()
    
    # Test with a transaction that has payment date = today
    print("8. Testing with TODAY's payment date...")
    today = date.today()
    today_transactions = purchases.filter(payment_date=today, is_reversed=False)
    print(f"   - Transactions due TODAY: {today_transactions.count()}")
    
    if today_transactions.count() > 0:
        for txn in today_transactions:
            print(f"     * {txn.transaction_number} - {txn.customer.name} - ৳{txn.amount}")
    
    # Test with overdue transactions
    print("\n9. Testing with OVERDUE payment dates...")
    overdue_transactions = purchases.filter(
        payment_date__lt=today,
        is_reversed=False
    ).order_by('payment_date')[:5]
    print(f"   - Overdue transactions (showing first 5): {overdue_transactions.count()}")
    
    if overdue_transactions.count() > 0:
        for txn in overdue_transactions:
            days_overdue = (today - txn.payment_date).days
            print(f"     * {txn.transaction_number} - {txn.customer.name} - {days_overdue} days overdue")
    
    print("\n" + "=" * 60)
    print("✅ NOTIFICATION SYSTEM VERIFICATION COMPLETE")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    try:
        test_notification_system()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)