#!/usr/bin/env python
"""Fix all purchase transactions' due_amount field"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
django.setup()

from transactions.models import Transaction, Customer
from decimal import Decimal

print('='*80)
print('FIXING ALL PURCHASE TRANSACTIONS DUE_AMOUNT')
print('='*80)

# Find all purchase transactions
purchases = Transaction.objects.filter(
    transaction_type='purchase',
    is_deleted=False,
    is_reversed=False
)

print(f'\nTotal purchase transactions: {purchases.count()}')

# Check and fix
fixed_count = 0
already_correct = 0

for p in purchases:
    expected_due = p.amount - p.cash_paid
    
    if p.due_amount != expected_due:
        p.due_amount = expected_due
        p.save(update_fields=['due_amount'])
        fixed_count += 1
        if fixed_count <= 5:  # Show first 5 fixes
            print(f'\n✓ Fixed {p.transaction_number}')
            print(f'  Customer: {p.customer.name}')
            print(f'  Amount: ৳{p.amount}, Cash: ৳{p.cash_paid}')
            print(f'  Due Amount: ৳{expected_due}')
    else:
        already_correct += 1

print(f'\n' + '='*80)
print(f'Total fixed: {fixed_count}')
print(f'Already correct: {already_correct}')
print('='*80)

# Now recalculate all customer balances
print('\nRecalculating customer balances...')
customers = Customer.objects.filter(is_deleted=False)
recalculated = 0

for customer in customers:
    old_balance = customer.current_balance
    new_balance = customer.recalculate_balance()
    customer.save()
    
    if old_balance != new_balance:
        recalculated += 1
        if recalculated <= 5:  # Show first 5 recalculations
            print(f'\n✓ {customer.name}')
            print(f'  Old Balance: ৳{old_balance}')
            print(f'  New Balance: ৳{new_balance}')

print(f'\n' + '='*80)
print(f'Total customers recalculated: {recalculated}/{customers.count()}')
print('='*80)
print('\n✓ All done!')
