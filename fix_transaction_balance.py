#!/usr/bin/env python
"""
Fix balance for transaction TXN-2026-00068 (ID: 77)
This transaction belongs to customer রাসেল মামা (01711645136)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
django.setup()

from transactions.models import Transaction, Customer

# Get the transaction
transaction = Transaction.objects.get(id=77)
print(f"Transaction: {transaction.transaction_number}")
print(f"Customer: {transaction.customer.name} ({transaction.customer.mobile})")
print(f"Type: {transaction.transaction_type}")
print(f"Amount: {transaction.amount}")
print(f"Current balance_before: {transaction.balance_before}")
print(f"Current balance_after: {transaction.balance_after}")
print(f"Is reversed: {transaction.is_reversed}")

# Get customer
customer = transaction.customer
print(f"\nCustomer current_balance: {customer.current_balance}")

# Check if this is the first transaction for this customer
previous_transactions = Transaction.objects.filter(
    customer=customer,
    is_deleted=False,
    created_at__lt=transaction.created_at
).order_by('-created_at')

if previous_transactions.exists():
    last_transaction = previous_transactions.first()
    print(f"\nPrevious transaction found:")
    print(f"  Transaction: {last_transaction.transaction_number}")
    print(f"  Balance after: {last_transaction.balance_after}")
    balance_before = last_transaction.balance_after
else:
    print(f"\nNo previous transactions found. This is the first transaction.")
    balance_before = 0

# Calculate correct balance_after
balance_after = balance_before + transaction.amount

print(f"\n--- Correction ---")
print(f"Correct balance_before should be: {balance_before}")
print(f"Correct balance_after should be: {balance_after}")

# Update the transaction
transaction.balance_before = balance_before
transaction.balance_after = balance_after
transaction.save()

print(f"\n✓ Transaction updated successfully!")
print(f"  balance_before: {transaction.balance_before}")
print(f"  balance_after: {transaction.balance_after}")

# Verify customer balance matches
if customer.current_balance != balance_after:
    print(f"\n⚠ Warning: Customer current_balance ({customer.current_balance}) doesn't match transaction balance_after ({balance_after})")
    print(f"Updating customer balance...")
    customer.current_balance = balance_after
    customer.save()
    print(f"✓ Customer balance updated to: {customer.current_balance}")
else:
    print(f"\n✓ Customer balance is correct: {customer.current_balance}")
