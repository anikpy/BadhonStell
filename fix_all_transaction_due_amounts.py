import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
django.setup()

from transactions.models import Customer, Transaction
from decimal import Decimal

print("=" * 80)
print("CHECK AND FIX ALL TRANSACTION DUE AMOUNTS")
print("=" * 80)

# Get all purchase transactions
purchase_transactions = Transaction.objects.filter(
    transaction_type='purchase',
    is_deleted=False,
    is_reversed=False
).exclude(status='cancelled')

print(f"\nTotal purchase transactions to check: {purchase_transactions.count()}")

issues_found = []

for txn in purchase_transactions:
    correct_due = txn.amount - txn.cash_paid
    
    if txn.due_amount != correct_due:
        issues_found.append({
            'transaction': txn,
            'current_due': txn.due_amount,
            'correct_due': correct_due,
            'difference': abs(txn.due_amount - correct_due)
        })

print(f"\nIssues found: {len(issues_found)}")

if issues_found:
    print("\n" + "=" * 80)
    print("TRANSACTIONS WITH INCORRECT DUE AMOUNTS:")
    print("=" * 80)
    
    for issue in issues_found:
        txn = issue['transaction']
        print(f"\nTransaction: {txn.transaction_number} (ID: {txn.pk})")
        print(f"  Customer: {txn.customer.name}")
        print(f"  Amount: ৳{txn.amount}")
        print(f"  Cash Paid: ৳{txn.cash_paid}")
        print(f"  Current Due: ৳{issue['current_due']}")
        print(f"  Should Be: ৳{issue['correct_due']}")
        print(f"  Difference: ৳{issue['difference']}")
    
    print(f"\n" + "=" * 80)
    print(f"Do you want to fix all {len(issues_found)} transactions? (y/n)")
    response = input().strip().lower()
    
    if response == 'y':
        print(f"\n✅ Fixing all transactions...")
        
        affected_customers = set()
        
        for issue in issues_found:
            txn = issue['transaction']
            old_due = txn.due_amount
            txn.due_amount = issue['correct_due']
            txn.save()
            
            affected_customers.add(txn.customer)
            
            print(f"  ✅ Fixed {txn.transaction_number}: ৳{old_due} → ৳{txn.due_amount}")
        
        print(f"\n✅ All transactions fixed!")
        print(f"\nRecalculating balances for {len(affected_customers)} affected customers...")
        
        for customer in affected_customers:
            old_balance = customer.current_balance
            new_balance = customer.recalculate_balance()
            customer.save()
            print(f"  {customer.name}: ৳{old_balance} → ৳{new_balance}")
        
        print(f"\n✅ All customer balances recalculated!")
    else:
        print(f"\n❌ Fix cancelled.")
else:
    print(f"\n✅ No issues found - all due amounts are correct!")

print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)

# Get summary statistics
total_customers = Customer.objects.filter(is_deleted=False).count()
customers_with_negative_balance = Customer.objects.filter(
    current_balance__lt=0,
    is_deleted=False
).count()
customers_with_positive_balance = Customer.objects.filter(
    current_balance__gt=0,
    is_deleted=False
).count()

print(f"\nTotal Customers: {total_customers}")
print(f"Customers with negative balance (owe money): {customers_with_negative_balance}")
print(f"Customers with positive balance (have credit): {customers_with_positive_balance}")

total_due = sum(
    abs(c.current_balance) for c in Customer.objects.filter(
        current_balance__lt=0,
        is_deleted=False
    )
)

print(f"\nTotal due from all customers: ৳{total_due}")
