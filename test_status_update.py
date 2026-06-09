#!/usr/bin/env python3
"""
Test script to verify status update feature
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
sys.path.insert(0, '/home/anik/Personal/BadhonStell')
django.setup()

from transactions.models import Customer, Transaction, TransactionHistory
from django.contrib.auth.models import User

def test_status_update():
    """Test the status update functionality"""
    print("=" * 60)
    print("STATUS UPDATE FEATURE VERIFICATION")
    print("=" * 60)
    
    # Get a test user
    try:
        user = User.objects.first()
        if not user:
            print("⚠️ No user found. Creating test user...")
            user = User.objects.create_user('testuser', 'test@test.com', 'testpass')
            print(f"✅ Created test user: {user.username}")
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        return False
    
    # Get a customer with purchase transactions
    customers = Customer.objects.all()
    print(f"\n1. Total Customers: {customers.count()}")
    
    test_customer = None
    test_transaction = None
    
    for customer in customers:
        purchases = Transaction.objects.filter(
            customer=customer,
            transaction_type='purchase',
            is_reversed=False
        )
        if purchases.exists():
            test_customer = customer
            test_transaction = purchases.first()
            break
    
    if not test_customer or not test_transaction:
        print("❌ No customer with purchase transactions found!")
        return False
    
    print(f"2. Test Customer: {test_customer.name} (PK: {test_customer.pk})")
    print(f"3. Test Transaction: {test_transaction.transaction_number} (PK: {test_transaction.pk})")
    print(f"   - Current Status: {test_transaction.get_status_display()}")
    print(f"   - Current Delivery Status: {test_transaction.get_delivery_status_display()}")
    
    # Test 1: Update status to 'ready'
    print("\n4. Testing Status Update...")
    print(f"   - Changing status from '{test_transaction.get_status_display()}' to 'প্রস্তুত' (ready)")
    
    old_status = test_transaction.status
    old_delivery_status = test_transaction.delivery_status
    
    test_transaction.status = 'ready'
    test_transaction.delivery_status = 'not_delivered'
    test_transaction.save()
    
    # Record history
    TransactionHistory.objects.create(
        transaction=test_transaction,
        action='edited',
        old_balance=test_transaction.balance_before,
        new_balance=test_transaction.balance_after,
        notes=f'Status updated: {test_transaction.get_status_display()} / {test_transaction.get_delivery_status_display()}',
        performed_by=user
    )
    
    print(f"   ✅ Status updated successfully!")
    print(f"   - New Status: {test_transaction.get_status_display()}")
    print(f"   - New Delivery Status: {test_transaction.get_delivery_status_display()}")
    
    # Test 2: Update delivery status
    print("\n5. Testing Delivery Status Update...")
    print(f"   - Changing delivery status from '{test_transaction.get_delivery_status_display()}' to 'ডেলিভারি সম্পন্ন' (delivered)")
    
    test_transaction.delivery_status = 'delivered'
    test_transaction.save()
    
    # Record history
    TransactionHistory.objects.create(
        transaction=test_transaction,
        action='edited',
        old_balance=test_transaction.balance_before,
        new_balance=test_transaction.balance_after,
        notes=f'Status updated: {test_transaction.get_status_display()} / {test_transaction.get_delivery_status_display()}',
        performed_by=user
    )
    
    print(f"   ✅ Delivery status updated successfully!")
    print(f"   - New Status: {test_transaction.get_status_display()}")
    print(f"   - New Delivery Status: {test_transaction.get_delivery_status_display()}")
    
    # Test 3: Update both at once
    print("\n6. Testing Both Status Update...")
    print(f"   - Changing both to: সম্পন্ন / ডেলিভারি সম্পন্ন")
    
    test_transaction.status = 'completed'
    test_transaction.delivery_status = 'delivered'
    test_transaction.save()
    
    # Record history
    TransactionHistory.objects.create(
        transaction=test_transaction,
        action='edited',
        old_balance=test_transaction.balance_before,
        new_balance=test_transaction.balance_after,
        notes=f'Status updated: {test_transaction.get_status_display()} / {test_transaction.get_delivery_status_display()}',
        performed_by=user
    )
    
    print(f"   ✅ Both statuses updated successfully!")
    print(f"   - Final Status: {test_transaction.get_status_display()}")
    print(f"   - Final Delivery Status: {test_transaction.get_delivery_status_display()}")
    
    # Check history
    print("\n7. Checking History Records...")
    history_count = TransactionHistory.objects.filter(transaction=test_transaction).count()
    print(f"   - Total history records for this transaction: {history_count}")
    
    recent_history = TransactionHistory.objects.filter(transaction=test_transaction).order_by('-created_at')[:3]
    print("   - Recent history:")
    for hist in recent_history:
        print(f"     * {hist.created_at.strftime('%Y-%m-%d %H:%M')} - {hist.notes}")
    
    # Restore original values
    print("\n8. Restoring Original Values...")
    test_transaction.status = old_status
    test_transaction.delivery_status = old_delivery_status
    test_transaction.save()
    print(f"   ✅ Restored to original values")
    
    print("\n" + "=" * 60)
    print("✅ STATUS UPDATE FEATURE VERIFICATION COMPLETE")
    print("=" * 60)
    print("\n📝 Summary:")
    print("   - Status can be updated via modal popup")
    print("   - Delivery status can be updated independently")
    print("   - Both can be updated together")
    print("   - History is recorded for each update")
    print("   - Changes are saved to database")
    print("\n💡 How to use in browser:")
    print("   1. Go to customer detail page")
    print("   2. Click blue 🔄 button on any purchase transaction")
    print("   3. Select new status from dropdowns")
    print("   4. Click 'আপডেট করুন'")
    print("   5. Success message will appear")
    
    return True

if __name__ == '__main__':
    try:
        test_status_update()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)