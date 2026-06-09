#!/usr/bin/env python3
"""
Fix balance calculation issue - recalculate all customer balances based on completed transactions
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
sys.path.insert(0, '/home/anik/Personal/BadhonStell')
django.setup()

from transactions.models import Customer, Transaction
from decimal import Decimal

def fix_customer_balances():
    """Recalculate all customer balances based on completed transactions"""
    print("=" * 70)
    print("FIXING CUSTOMER BALANCE CALCULATIONS")
    print("=" * 70)
    
    customers = Customer.objects.all()
    total_customers = customers.count()
    fixed_count = 0
    
    for idx, customer in enumerate(customers, 1):
        print(f"\n[{idx}/{total_customers}] Processing: {customer.name} ({customer.mobile_number})")
        
        # Get all completed, non-reversed transactions for this customer
        transactions = Transaction.objects.filter(
            customer=customer,
            is_reversed=False
        ).order_by('created_at')
        
        # Calculate correct balance
        correct_balance = Decimal('0.00')
        
        for txn in transactions:
            if txn.transaction_type == 'submission':
                correct_balance += txn.amount
            elif txn.transaction_type in ['purchase', 'withdrawal']:
                correct_balance -= abs(txn.amount)
            elif txn.transaction_type == 'adjustment':
                correct_balance += txn.amount
            elif txn.transaction_type == 'reversal':
                if txn.reverses_transaction:
                    if txn.reverses_transaction.transaction_type == 'submission':
                        correct_balance -= abs(txn.reverses_transaction.amount)
                    else:
                        correct_balance += abs(txn.reverses_transaction.amount)
        
        old_balance = customer.current_balance
        
        if old_balance != correct_balance:
            print(f"  ❌ Balance mismatch detected!")
            print(f"     Old balance: ৳{old_balance}")
            print(f"     Correct balance: ৳{correct_balance}")
            print(f"     Difference: ৳{correct_balance - old_balance}")
            
            # Update customer balance
            customer.current_balance = correct_balance
            customer.save()
            
            print(f"  ✅ Balance fixed!")
            fixed_count += 1
        else:
            print(f"  ✅ Balance is correct: ৳{correct_balance}")
    
    print("\n" + "=" * 70)
    print(f"SUMMARY: Fixed {fixed_count} out of {total_customers} customers")
    print("=" * 70)

if __name__ == '__main__':
    try:
        fix_customer_balances()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
