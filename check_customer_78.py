#!/usr/bin/env python
"""Script to check customer 78 data"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
django.setup()

from transactions.models import Customer, Transaction
from decimal import Decimal

customer = Customer.objects.get(id=78)
print(f'Customer: {customer.name}')
print(f'Mobile: {customer.mobile_number}')
print(f'Current Balance: ৳{customer.current_balance}')
print('\n' + '='*80)
print('TRANSACTIONS:')
print('='*80)

transactions = customer.transactions.filter(is_deleted=False, is_reversed=False).order_by('order_date')
print(f'Total transactions: {transactions.count()}\n')

total_submitted = Decimal('0')
total_purchased = Decimal('0')
total_withdrawn = Decimal('0')

for t in transactions:
    print(f'Transaction: {t.transaction_number}')
    print(f'  Type: {t.transaction_type}')
    print(f'  Amount: ৳{t.amount}')
    print(f'  Status: {t.status}')
    print(f'  Cash Paid: ৳{t.cash_paid}')
    print(f'  Due Amount: ৳{t.due_amount}')
    print(f'  Order Date: {t.order_date}')
    print(f'  Balance After: ৳{t.balance_after}')
    print('-' * 40)
    
    if t.transaction_type == 'submission':
        total_submitted += t.amount
    elif t.transaction_type == 'purchase':
        total_purchased += t.amount
    elif t.transaction_type == 'withdrawal':
        total_withdrawn += abs(t.amount)

print('\n' + '='*80)
print('TOTALS:')
print('='*80)
print(f'Total Submitted (জমা): ৳{total_submitted}')
print(f'Total Purchased (ক্রয়): ৳{total_purchased}')
print(f'Total Withdrawn (উত্তোলন): ৳{total_withdrawn}')
print(f'Net Balance: ৳{total_submitted - total_purchased - total_withdrawn}')
print('='*80)

# Check purchase transactions specifically
print('\n' + '='*80)
print('PURCHASE DETAILS:')
print('='*80)
purchases = transactions.filter(transaction_type='purchase')
print(f'Total purchase transactions: {purchases.count()}\n')
for p in purchases:
    print(f'Purchase: {p.transaction_number}')
    print(f'  Amount: ৳{p.amount}')
    print(f'  Status: {p.status}')
    print(f'  Items count: {p.items.count()}')
    if p.items.count() > 0:
        for item in p.items.all():
            print(f'    - {item.product_name}: {item.quantity} × ৳{item.unit_price} = ৳{item.net_amount}')
    print()
