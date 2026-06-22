import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
django.setup()

from transactions.models import Customer, Transaction
from decimal import Decimal

print("=" * 80)
print("FIX TRANSACTION 109 - DUE AMOUNT")
print("=" * 80)

# Get transaction 109
transaction = Transaction.objects.get(pk=109)
customer = transaction.customer

print(f"\nCustomer: {customer.name} (ID: {customer.pk})")
print(f"\nTransaction Details:")
print(f"  ID: {transaction.pk}")
print(f"  Number: {transaction.transaction_number}")
print(f"  Type: {transaction.transaction_type}")
print(f"  Amount: ৳{transaction.amount}")
print(f"  Cash Paid: ৳{transaction.cash_paid}")
print(f"  Due Amount (CURRENT): ৳{transaction.due_amount}")

# Calculate correct due amount
correct_due_amount = transaction.amount - transaction.cash_paid

print(f"  Due Amount (SHOULD BE): ৳{correct_due_amount}")

print(f"\nCustomer Balance (BEFORE FIX): ৳{customer.current_balance}")

if transaction.due_amount != correct_due_amount:
    print(f"\n⚠️  MISMATCH DETECTED!")
    print(f"   Difference: ৳{abs(transaction.due_amount - correct_due_amount)}")
    
    # Ask for confirmation
    print(f"\nDo you want to fix this? (y/n)")
    response = input().strip().lower()
    
    if response == 'y':
        print(f"\n✅ Fixing transaction 109...")
        
        # Update due amount
        transaction.due_amount = correct_due_amount
        transaction.save()
        
        print(f"✅ Transaction updated!")
        print(f"   New due_amount: ৳{transaction.due_amount}")
        
        # Recalculate customer balance
        customer.refresh_from_db()
        print(f"\n✅ Customer balance recalculated!")
        print(f"   Old balance: ৳{customer.current_balance}")
        
        new_balance = customer.recalculate_balance()
        customer.save()
        customer.refresh_from_db()
        
        print(f"   New balance: ৳{customer.current_balance}")
        
        print(f"\n✅ Fix completed successfully!")
    else:
        print(f"\n❌ Fix cancelled.")
else:
    print(f"\n✅ No fix needed - due amount is correct!")

print("\n" + "=" * 80)
print("VERIFICATION:")
print("=" * 80)

# Verify all transactions for this customer
print(f"\nAll transactions for {customer.name}:")
for txn in customer.transactions.filter(is_deleted=False, is_reversed=False).order_by('created_at'):
    print(f"\n  {txn.transaction_number}:")
    print(f"    Type: {txn.transaction_type}")
    print(f"    Amount: ৳{txn.amount}")
    if txn.transaction_type == 'purchase':
        print(f"    Cash Paid: ৳{txn.cash_paid}")
        print(f"    Due Amount: ৳{txn.due_amount}")
        print(f"    Correct?: {'✅' if txn.due_amount == (txn.amount - txn.cash_paid) else '❌'}")

print(f"\nTotal Purchase Amount: ৳{customer.total_purchase_amount}")
print(f"Total Submitted: ৳{customer.total_submitted}")
print(f"Total Withdrawn: ৳{customer.total_withdrawn}")
print(f"Current Balance: ৳{customer.current_balance}")

if customer.current_balance < 0:
    print(f"Customer owes: ৳{abs(customer.current_balance)} (বাকি)")
elif customer.current_balance > 0:
    print(f"Customer has credit: ৳{customer.current_balance} (কাস্টমার পাবে)")
else:
    print(f"Balance is zero - all settled")
