#!/usr/bin/env python3
"""
Script to delete all orders for customer 46 except the 20400 tk order
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from transactions.models import Customer, Transaction

def cleanup_customer_orders():
    """Delete all orders for customer 46 except the 20400 tk order"""
    
    try:
        # Get customer 46
        customer = Customer.objects.get(pk=46)
        print(f"Found customer: {customer.name} (ID: {customer.pk})")
        print(f"Current balance: ৳{customer.current_balance}")
        print()
        
        # Get all transactions for this customer
        all_transactions = customer.transactions.all().order_by('-created_at')
        print(f"Total transactions found: {all_transactions.count()}")
        print()
        
        # Display all transactions
        print("All transactions:")
        print("-" * 80)
        for txn in all_transactions:
            print(f"ID: {txn.pk:3d} | Type: {txn.transaction_type:12s} | Amount: ৳{txn.amount:10.2f} | Status: {txn.status:10s} | Reversed: {txn.is_reversed}")
        print("-" * 80)
        print()
        
        # Find the 20400 tk order
        target_order = all_transactions.filter(amount=20400).first()
        
        if not target_order:
            print("❌ ERROR: No order found with amount 20400 tk!")
            print("Available amounts:")
            amounts = all_transactions.values_list('amount', flat=True).distinct()
            for amt in amounts:
                print(f"  - ৳{amt}")
            return False
        
        print(f"✅ Found target order: ID {target_order.pk} - ৳{target_order.amount} ({target_order.transaction_type})")
        print()
        
        # Get orders to delete (all except the target)
        orders_to_delete = all_transactions.exclude(pk=target_order.pk)
        
        if orders_to_delete.count() == 0:
            print("✅ No orders to delete. Only the 20400 tk order exists.")
            return True
        
        print(f"Orders to DELETE ({orders_to_delete.count()}):")
        print("-" * 80)
        for txn in orders_to_delete:
            print(f"ID: {txn.pk:3d} | Type: {txn.transaction_type:12s} | Amount: ৳{txn.amount:10.2f} | Status: {txn.status:10s}")
        print("-" * 80)
        print()
        
        # Auto-confirm deletion (non-interactive mode)
        print(f"⚠️  PERMANENTLY DELETING {orders_to_delete.count()} orders...")
        print()
        
        # Delete orders
        deleted_count = 0
        for txn in orders_to_delete:
            txn_info = f"ID {txn.pk} - ৳{txn.amount} ({txn.transaction_type})"
            print(f"Deleting: {txn_info}...", end=" ")
            txn.delete()
            deleted_count += 1
            print("✅")
        
        print()
        print(f"✅ Successfully deleted {deleted_count} orders!")
        print()
        
        # Show remaining orders
        remaining = customer.transactions.all()
        print(f"Remaining orders for {customer.name}: {remaining.count()}")
        print("-" * 80)
        for txn in remaining:
            print(f"ID: {txn.pk:3d} | Type: {txn.transaction_type:12s} | Amount: ৳{txn.amount:10.2f} | Status: {txn.status:10s}")
        print("-" * 80)
        print()
        
        # Recalculate customer balance
        print("Recalculating customer balance...")
        from django.db.models import Sum
        
        total_submitted = customer.transactions.filter(
            transaction_type='submission',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_purchased = customer.transactions.filter(
            transaction_type='purchase',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        total_withdrawn = customer.transactions.filter(
            transaction_type='withdrawal',
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate new balance: submitted - purchased - withdrawn
        new_balance = total_submitted - abs(total_purchased) - abs(total_withdrawn)
        
        print(f"  Total Submitted: ৳{total_submitted}")
        print(f"  Total Purchased: ৳{abs(total_purchased)}")
        print(f"  Total Withdrawn: ৳{abs(total_withdrawn)}")
        print(f"  New Balance: ৳{new_balance}")
        print()
        
        customer.current_balance = new_balance
        customer.save()
        
        print(f"✅ Customer balance updated to: ৳{customer.current_balance}")
        print()
        print("✅ Cleanup completed successfully!")
        
        return True
        
    except Customer.DoesNotExist:
        print(f"❌ ERROR: Customer with ID 46 not found!")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 80)
    print("CUSTOMER ORDER CLEANUP SCRIPT")
    print("=" * 80)
    print()
    
    success = cleanup_customer_orders()
    
    print()
    print("=" * 80)
    if success:
        print("✅ Script completed successfully")
    else:
        print("❌ Script failed")
    print("=" * 80)