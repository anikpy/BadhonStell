#!/usr/bin/env python3
"""
Fix customer 46 balance - recalculate with new logic (include pending orders)
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from transactions.models import Customer, Transaction
from django.db.models import Sum

def fix_balance():
    try:
        customer = Customer.objects.get(pk=46)
        
        print("=" * 80)
        print(f"CUSTOMER: {customer.name} (ID: {customer.pk})")
        print("=" * 80)
        print()
        
        # Get all non-reversed transactions (including pending)
        transactions = customer.transactions.filter(is_reversed=False).order_by('-created_at')
        
        print("NON-REVERSED TRANSACTIONS:")
        print("-" * 80)
        for txn in transactions:
            print(f"ID: {txn.pk:3d} | Type: {txn.transaction_type:12s} | Amount: ৳{txn.amount:10.2f} | Status: {txn.status:10s}")
        print("-" * 80)
        print()
        
        # Calculate totals (excluding reversals)
        total_submission = transactions.filter(transaction_type='submission').aggregate(total=Sum('amount'))['total'] or 0
        total_purchase = transactions.filter(transaction_type='purchase').aggregate(total=Sum('amount'))['total'] or 0
        total_withdrawal = transactions.filter(transaction_type='withdrawal').aggregate(total=Sum('amount'))['total'] or 0
        
        print("TOTALS (excluding reversals):")
        print(f"  Total Submissions: ৳{total_submission}")
        print(f"  Total Purchases: ৳{total_purchase}")
        print(f"  Total Withdrawals: ৳{total_withdrawal}")
        print()
        
        # Calculate expected balance
        # Balance = submissions - purchases - withdrawals
        expected_balance = total_submission - abs(total_purchase) - abs(total_withdrawal)
        
        print(f"CALCULATION: {total_submission} - {abs(total_purchase)} - {abs(total_withdrawal)}")
        print(f"EXPECTED BALANCE: ৳{expected_balance}")
        print()
        
        print(f"CURRENT BALANCE: ৳{customer.current_balance}")
        print()
        
        if customer.current_balance != expected_balance:
            print("⚠️  Balance mismatch! Updating...")
            customer.current_balance = expected_balance
            customer.save()
            print(f"✅ Balance updated to: ৳{customer.current_balance}")
        else:
            print("✅ Balance is already correct")
        
        print()
        print("=" * 80)
        print("SUMMARY:")
        print("=" * 80)
        print(f"Customer: {customer.name}")
        print(f"Total Orders: {transactions.count()}")
        print(f"Total Purchases: ৳{abs(total_purchase)} (this is the DUE amount)")
        print(f"Total Submissions: ৳{total_submission}")
        print(f"Current Balance: ৳{customer.current_balance}")
        print()
        print("NOTE: Negative balance means customer owes money (due amount)")
        print("=" * 80)
        
    except Customer.DoesNotExist:
        print(f"❌ Customer ID 46 not found!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    fix_balance()