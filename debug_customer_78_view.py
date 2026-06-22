#!/usr/bin/env python
"""Debug script to test customer 78 statement calculation"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
django.setup()

from transactions.models import Customer, Transaction
from decimal import Decimal
from django.db.models import Sum

customer = Customer.objects.get(id=78)
print(f'Customer: {customer.name}')
print('='*80)

# Replicate the view's logic
transactions = customer.transactions.filter(is_deleted=False, is_reversed=False).order_by('order_date')

print(f'\nTotal transactions: {transactions.count()}')

# Calculate totals like the view does
print('\n' + '='*80)
print('VIEW CALCULATION (as currently coded):')
print('='*80)

total_submitted = transactions.filter(transaction_type='submission').aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
print(f'total_submitted: {total_submitted}')

purchases = transactions.filter(transaction_type='purchase')
print(f'\npurchases queryset: {purchases}')
print(f'purchases count: {purchases.count()}')
print(f'purchases query: {purchases.query}')

print('\nIterating purchases:')
for p in purchases:
    print(f'  - {p.transaction_number}: amount={p.amount}, type={type(p.amount)}')

total_purchased = sum(p.amount for p in purchases)
print(f'\ntotal_purchased (using sum): {total_purchased}')
print(f'total_purchased type: {type(total_purchased)}')

# Try alternative calculation
total_purchased_aggregate = purchases.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
print(f'total_purchased (using aggregate): {total_purchased_aggregate}')

total_withdrawn = transactions.filter(transaction_type='withdrawal').aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
total_withdrawn = abs(total_withdrawn)
print(f'total_withdrawn: {total_withdrawn}')

print('\n' + '='*80)
print('RESULTS:')
print('='*80)
print(f'মোট জমা (Total Submitted): ৳{total_submitted}')
print(f'মোট ক্রয় (Total Purchased): ৳{total_purchased}')
print(f'মোট উত্তোলন (Total Withdrawn): ৳{total_withdrawn}')
print(f'Net Balance: ৳{total_submitted - total_purchased - total_withdrawn}')
