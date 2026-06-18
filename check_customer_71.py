#!/usr/bin/env python3
"""
Check customer ID 71 specifically
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
django.setup()

from transactions.models import Customer, Transaction
from decimal import Decimal

print("=" * 80)
print("Checking Customer ID: 71")
print("=" * 80)

try:
    customer = Customer.objects.get(pk=71)
    print(f"Customer: {customer.name} (ID: {customer.pk})")
    print(f"Mobile: {customer.mobile_number}")
    print(f"Current Balance: ৳{customer.current_balance:.2f}")
    
    # Get all transactions for this customer
    transactions = customer.transactions.filter(is_deleted=False, is_reversed=False).order_by('created_at')
    
    print(f"\nTotal Transactions: {transactions.count()}")
    print("-" * 80)
    
    # Analyze each transaction
    running_balance = Decimal('0.00')
    for i, txn in enumerate(transactions, 1):
        print(f"{i:3d}. {txn.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"     Type: {txn.get_transaction_type_display()}")
        print(f"     Amount: ৳{txn.amount:.2f}")
        
        # For purchase transactions, show cash paid and due
        if txn.transaction_type == 'purchase':
            print(f"     Cash Paid: ৳{getattr(txn, 'cash_paid', 0):.2f}")
            print(f"     Due Amount: ৳{getattr(txn, 'due_amount', txn.amount):.2f}")
        
        print(f"     Balance Before: ৳{txn.balance_before:.2f}")
        print(f"     Balance After: ৳{txn.balance_after:.2f}")
        print(f"     Status: {txn.status}")
        print()
        
        # Calculate manually
        if txn.transaction_type == 'submission':
            running_balance += txn.amount
        elif txn.transaction_type == 'purchase':
            due = getattr(txn, 'due_amount', txn.amount)
            running_balance -= due
        elif txn.transaction_type == 'withdrawal':
            running_balance -= abs(txn.amount)
    
    print(f"\nManual Calculation: ৳{running_balance:.2f}")
    print(f"Database Balance: ৳{customer.current_balance:.2f}")
    print(f"Match: {'✅ YES' if running_balance == customer.current_balance else '❌ NO'}")
    
    # Check for purchases with cash paid
    purchases = transactions.filter(transaction_type='purchase')
    print(f"\nPurchase Transactions: {purchases.count()}")
    for purchase in purchases:
        cash_paid = getattr(purchase, 'cash_paid', 0)
        due_amount = getattr(purchase, 'due_amount', purchase.amount)
        print(f"  - Purchase: ৳{purchase.amount:.2f}, Cash Paid: ৳{cash_paid:.2f}, Due: ৳{due_amount:.2f}")
    
except Customer.DoesNotExist:
    print("❌ Customer with ID 71 not found!")
    
print("\n" + "=" * 80)
print("Recalculation test")
print("=" * 80)

if 'customer' in locals():
    old_balance = customer.current_balance
    customer.recalculate_balance()
    print(f"Old balance: ৳{old_balance:.2f}")
    print(f"New balance: ৳{customer.current_balance:.2f}")
    if old_balance != customer.current_balance:
        print("⚠️  Balance changed! Saving...")
        customer.save()
    else:
        print("✅ Balance is already correct")
else:
    print("Customer not found, skipping recalculation")