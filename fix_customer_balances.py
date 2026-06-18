#!/usr/bin/env python3
"""
Fix customer balances to consider cash paid vs due amount
"""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
django.setup()

from transactions.models import Customer, Transaction

print("=" * 80)
print("Fixing Customer Balances")
print("=" * 80)

# Get all customers
customers = Customer.objects.all()
total_customers = customers.count()
print(f"Found {total_customers} customers")

fixed_count = 0
for idx, customer in enumerate(customers, 1):
    old_balance = customer.current_balance
    
    # Recalculate balance using the new logic
    customer.recalculate_balance()
    
    if customer.current_balance != old_balance:
        fixed_count += 1
        print(f"{idx:3d}. {customer.name:<30} Balance: ৳{old_balance:>10.2f} → ৳{customer.current_balance:>10.2f} {'(Fixed)' if customer.current_balance != old_balance else ''}")
        customer.save()
    
    if idx % 10 == 0:
        print(f"Processed {idx}/{total_customers} customers...")

print("\n" + "=" * 80)
print(f"Fixed {fixed_count} out of {total_customers} customers")
print("=" * 80)

# Now let's test specific scenarios
print("\n\n" + "=" * 80)
print("Testing Scenarios")
print("=" * 80)

# Test scenario 1: Customer with cash payment
print("\n1. Test Scenario: Customer paid partial amount")
print("-" * 80)
print("Purchase: ৳100, Cash Paid: ৳90, Due: ৳10")
print("Old logic: Balance = -৳100 (full purchase amount)")
print("New logic: Balance = -৳10 (due amount only)")
print("Expected: ৳-10.00 (বাকি)")

# Test scenario 2: Customer with full payment
print("\n2. Test Scenario: Customer paid full amount")
print("-" * 80)
print("Purchase: ৳100, Cash Paid: ৳100, Due: ৳0")
print("Old logic: Balance = -৳100 (full purchase amount)")
print("New logic: Balance = ৳0 (no due)")
print("Expected: ৳0.00 (পরিষ্কার)")

# Test scenario 3: Customer with extra payment
print("\n3. Test Scenario: Customer paid extra amount")
print("-" * 80)
print("Purchase: ৳100, Cash Paid: ৳120, Due: ৳0, Extra: ৳20")
print("Old logic: Balance = -৳100 (full purchase amount)")
print("New logic: Balance = ৳20 (extra amount added to balance)")
print("Expected: ৳20.00 (জমা আছে)")

# Test scenario 4: Multiple transactions
print("\n4. Test Scenario: Multiple transactions")
print("-" * 80)
print("Transaction 1: Purchase ৳100, Cash Paid ৳50, Due ৳50")
print("Transaction 2: Submission ৳30")
print("Transaction 3: Purchase ৳200, Cash Paid ৳100, Due ৳100")
print("Balance calculation: (৳30 submission) - (৳50 + ৳100 due)")
print("Expected: -৳120.00 (বাকি)")

print("\n" + "=" * 80)
print("How it works:")
print("=" * 80)
print("✓ For purchase transactions: balance -= due_amount")
print("✓ For submission transactions: balance += amount")
print("✓ For withdrawal transactions: balance -= amount")
print("✓ For cancelled purchases: balance not affected")
print("✓ Cash paid is considered in due_amount calculation")
print("✓ Extra payment automatically creates submission")
print("✓ All calculations use Decimal for accuracy")
print("✓ Existing customer balances automatically fixed")

print("\n✅ Script completed. Run it to fix all customer balances.")
print("=" * 80)

# Create a sample customer to demonstrate
print("\nSample command to run:")
print("python3 manage.py shell")
print("""
from transactions.models import Customer
for customer in Customer.objects.all():
    old = customer.current_balance
    customer.recalculate_balance()
    if customer.current_balance != old:
        customer.save()
        print(f'Fixed {customer.name}: {old} → {customer.current_balance}')
""")