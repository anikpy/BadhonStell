#!/usr/bin/env python3
"""
Debug script for customer 46 - check transactions and balance
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from transactions.models import Customer, Transaction
from django.db.models import Sum

def debug_customer():
    try:
        customer = Customer.objects.get(pk=46)
        
        print("=" * 80)
        print(f"CUSTOMER: {customer.name} (ID: {customer.pk})")
        print("=" * 80)
        print(f"Current Balance in DB: ৳{customer.current_balance}")
        print()
        
        # Get all transactions
        transactions = customer.transactions.all().order_by('-created_at')
        print(f"Total Transactions: {transactions.count()}")
        print()
        
        print("ALL TRANSACTIONS:")
        print("-" * 80)
        for txn in transactions:
            print(f"ID: {txn.pk:3d} | Type: {txn.transaction_type:12s} | Amount: ৳{txn.amount:10.2f}")
            print(f"         Status: {txn.status:10s} | Reversed: {txn.is_reversed}")
            print(f"         Balance Before: ৳{txn.balance_before:10.2f} | Balance After: ৳{txn.balance_after:10.2f}")
            print(f"         Created: {txn.created_at}")
            if txn.transaction_type == 'purchase':
                print(f"         Item: {txn.item_name}")
            print()
        
        print("-" * 80)
        print()
        
        # Calculate what balance should be (using NEW logic - exclude reversals only)
        print("CALCULATING EXPECTED BALANCE:")
        print("-" * 80)
        
        # Get non-reversed transactions only
        non_reversed = transactions.filter(is_reversed=False)
        
        total_submission = non_reversed.filter(
            transaction_type='submission'
        ).aggregate(total=Sum('amount'))['total'] or 0
        print(f"Total Submissions (not reversed): ৳{total_submission}")
        
        total_purchase = non_reversed.filter(
            transaction_type='purchase'
        ).aggregate(total=Sum('amount'))['total'] or 0
        print(f"Total Purchases (not reversed): ৳{total_purchase}")
        
        total_withdrawal = non_reversed.filter(
            transaction_type='withdrawal'
        ).aggregate(total=Sum('amount'))['total'] or 0
        print(f"Total Withdrawals (not reversed): ৳{total_withdrawal}")
        
        print()
        
        # Expected balance calculation (simple: submissions - purchases - withdrawals)
        expected_balance = total_submission - abs(total_purchase) - abs(total_withdrawal)
        print(f"EXPECTED BALANCE = {total_submission} - {abs(total_purchase)} - {abs(total_withdrawal)}")
        print(f"EXPECTED BALANCE: ৳{expected_balance}")
        print()
        
        print("=" * 80)
        print(f"ACTUAL BALANCE:   ৳{customer.current_balance}")
        print(f"EXPECTED BALANCE: ৳{expected_balance}")
        
        if customer.current_balance != expected_balance:
            print("❌ BALANCE MISMATCH!")
        else:
            print("✅ Balance is correct")
        print("=" * 80)
        
    except Customer.DoesNotExist:
        print(f"❌ Customer ID 46 not found!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_customer()