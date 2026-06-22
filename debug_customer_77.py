import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
django.setup()

from transactions.models import Customer, Transaction
from decimal import Decimal

# Get customer 77
customer = Customer.objects.get(pk=77)

print("=" * 80)
print(f"CUSTOMER: {customer.name} (ID: {customer.pk})")
print(f"Mobile: {customer.mobile_number}")
print("=" * 80)

# Get all transactions (including deleted and reversed)
all_transactions = customer.transactions.all().order_by('created_at')
print(f"\nTotal transactions (including deleted/reversed): {all_transactions.count()}")

# Get ACTIVE transactions (non-deleted, non-reversed)
active_transactions = customer.transactions.filter(
    is_deleted=False,
    is_reversed=False
).order_by('created_at')
print(f"Active transactions (non-deleted, non-reversed): {active_transactions.count()}")

print("\n" + "=" * 80)
print("ALL TRANSACTIONS:")
print("=" * 80)

for txn in all_transactions:
    print(f"\nID: {txn.pk}")
    print(f"  Number: {txn.transaction_number}")
    print(f"  Type: {txn.transaction_type}")
    print(f"  Amount: ৳{txn.amount}")
    print(f"  Status: {txn.status}")
    print(f"  Is Deleted: {txn.is_deleted}")
    print(f"  Is Reversed: {txn.is_reversed}")
    if txn.transaction_type == 'purchase':
        print(f"  Cash Paid: ৳{txn.cash_paid}")
        print(f"  Due Amount: ৳{txn.due_amount}")
    print(f"  Date: {txn.order_date if hasattr(txn, 'order_date') else txn.created_at}")

print("\n" + "=" * 80)
print("ACTIVE TRANSACTIONS ONLY:")
print("=" * 80)

for txn in active_transactions:
    print(f"\nID: {txn.pk}")
    print(f"  Number: {txn.transaction_number}")
    print(f"  Type: {txn.transaction_type}")
    print(f"  Amount: ৳{txn.amount}")
    print(f"  Status: {txn.status}")
    if txn.transaction_type == 'purchase':
        print(f"  Cash Paid: ৳{txn.cash_paid}")
        print(f"  Due Amount: ৳{txn.due_amount}")

print("\n" + "=" * 80)
print("CALCULATED TOTALS:")
print("=" * 80)

# Manually calculate totals
total_submissions = Decimal('0')
total_purchases = Decimal('0')
total_withdrawals = Decimal('0')
total_cash_paid = Decimal('0')
total_due = Decimal('0')

for txn in active_transactions:
    if txn.transaction_type == 'submission':
        total_submissions += txn.amount
    elif txn.transaction_type == 'purchase' and txn.status != 'cancelled':
        total_purchases += txn.amount
        total_cash_paid += txn.cash_paid
        total_due += txn.due_amount
    elif txn.transaction_type == 'withdrawal':
        total_withdrawals += abs(txn.amount)

print(f"\nTotal Submissions (Deposits): ৳{total_submissions}")
print(f"Total Purchases (Full Amount): ৳{total_purchases}")
print(f"Total Cash Paid: ৳{total_cash_paid}")
print(f"Total Due from Purchases: ৳{total_due}")
print(f"Total Withdrawals: ৳{total_withdrawals}")

print("\n" + "=" * 80)
print("BALANCE CALCULATION:")
print("=" * 80)

# Method 1: Using due_amount
balance_method_1 = total_submissions - total_due - total_withdrawals
print(f"\nMethod 1 (Submissions - Due - Withdrawals):")
print(f"  {total_submissions} - {total_due} - {total_withdrawals} = ৳{balance_method_1}")

# Method 2: Using full purchase amount minus cash paid
balance_method_2 = total_submissions - (total_purchases - total_cash_paid) - total_withdrawals
print(f"\nMethod 2 (Submissions - (Purchases - Cash Paid) - Withdrawals):")
print(f"  {total_submissions} - ({total_purchases} - {total_cash_paid}) - {total_withdrawals} = ৳{balance_method_2}")

print("\n" + "=" * 80)
print("CUSTOMER MODEL PROPERTIES:")
print("=" * 80)

print(f"\ncustomer.total_submitted: ৳{customer.total_submitted}")
print(f"customer.total_purchased: ৳{customer.total_purchased}")
print(f"customer.total_purchase_amount: ৳{customer.total_purchase_amount}")
print(f"customer.total_withdrawn: ৳{customer.total_withdrawn}")
print(f"customer.current_balance (from DB): ৳{customer.current_balance}")

print("\n" + "=" * 80)
print("RECALCULATE BALANCE:")
print("=" * 80)

# Test recalculate
calculated_balance = customer.recalculate_balance()
print(f"\nRecalculated balance: ৳{calculated_balance}")
print(f"Current balance in DB: ৳{customer.current_balance}")

if calculated_balance != customer.current_balance:
    print(f"\n⚠️  WARNING: Mismatch detected!")
    print(f"   Calculated: ৳{calculated_balance}")
    print(f"   In Database: ৳{customer.current_balance}")
    print(f"   Difference: ৳{abs(calculated_balance - customer.current_balance)}")
else:
    print(f"\n✅ Balance matches!")

print("\n" + "=" * 80)
print("ANALYSIS:")
print("=" * 80)

if customer.current_balance < 0:
    print(f"\n❌ Customer owes: ৳{abs(customer.current_balance)} (বাকি)")
elif customer.current_balance > 0:
    print(f"\n✅ Customer has credit: ৳{customer.current_balance} (কাস্টমার পাবে)")
else:
    print(f"\n✅ Balance is zero - all settled")

# Check for potential issues
print("\n" + "=" * 80)
print("POTENTIAL ISSUES CHECK:")
print("=" * 80)

# Check for hardcoded values
print("\nChecking for customer ID 77 specific code...")
print("Searching in models.py, views.py...")

# Check if customer 77 has any special handling
if customer.pk == 77 and customer.name == "Badhon Steel (Dukan)":
    print(f"\n⚠️  This is a special customer: {customer.name}")
    print("   This might be the shop's own account - check if there's special logic")
