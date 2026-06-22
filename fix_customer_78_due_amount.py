#!/usr/bin/env python
"""Fix customer 78's purchase due_amount"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
django.setup()

from transactions.models import Customer, Transaction
from decimal import Decimal

customer = Customer.objects.get(id=78)
print(f'Customer: {customer.name}')
print(f'Current Balance: ৳{customer.current_balance}')
print('\n' + '='*80)
print('Fixing purchase due_amount...')
print('='*80)

purchases = customer.transactions.filter(transaction_type='purchase', is_deleted=False, is_reversed=False)

for p in purchases:
    print(f'\nTransaction: {p.transaction_number}')
    print(f'  Amount: ৳{p.amount}')
    print(f'  Cash Paid: ৳{p.cash_paid}')
    print(f'  Due Amount (OLD): ৳{p.due_amount}')
    
    # Calculate correct due amount
    correct_due = p.amount - p.cash_paid
    print(f'  Due Amount (NEW): ৳{correct_due}')
    
    if p.due_amount != correct_due:
        p.due_amount = correct_due
        p.save()
        print(f'  ✓ Updated!')
    else:
        print(f'  Already correct')

print('\n' + '='*80)
print('Recalculating customer balance...')
print('='*80)

# Recalculate balance
new_balance = customer.recalculate_balance()
customer.save()

print(f'New Balance: ৳{new_balance}')
print('\n' + '='*80)
print('Verification:')
print('='*80)
customer.refresh_from_db()
print(f'Total Submitted: ৳{customer.total_submitted}')
print(f'Total Purchased: ৳{customer.total_purchased}')
print(f'Total Withdrawn: ৳{customer.total_withdrawn}')
print(f'Current Balance: ৳{customer.current_balance}')
print(f'\nExpected Balance: {customer.total_submitted} - {customer.total_purchased} - {customer.total_withdrawn} = ৳{customer.total_submitted - customer.total_purchased - customer.total_withdrawn}')
