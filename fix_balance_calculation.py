#!/usr/bin/env python3
"""
Fix balance calculation issue - recalculate all customer balances based on ACTIVE transactions only.

This script implements the correct balance calculation rules:
1. মোট জমা (Total Deposits) = Sum of all non-reversed submissions
2. মোট ক্রয় (Total Purchases) = Sum of all ACTIVE orders (non-reversed, non-cancelled)
3. মোট উত্তোলন (Total Withdrawals) = Sum of all non-reversed withdrawals
4. বর্তমান ব্যালেন্স = মোট জমা - মোট ক্রয় - মোট উত্তোলন

Key fixes:
- Cancelled orders are now EXCLUDED from balance calculations
- Reversed transactions are EXCLUDED from balance calculations
- Deleted transactions are EXCLUDED from balance calculations
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
sys.path.insert(0, '/home/anik/Personal/BadhonStell')
django.setup()

from transactions.models import Customer, Transaction
from decimal import Decimal

def fix_customer_balances():
    """Recalculate all customer balances based on ACTIVE transactions only"""
    print("=" * 80)
    print("FIXING CUSTOMER BALANCE CALCULATIONS")
    print("=" * 80)
    print("\nBalance Calculation Rules:")
    print("- মোট জমা (Total Deposits) = Sum of all non-reversed submissions")
    print("- মোট ক্রয় (Total Purchases) = Sum of ACTIVE orders (non-reversed, non-cancelled)")
    print("- মোট উত্তোলন (Total Withdrawals) = Sum of all non-reversed withdrawals")
    print("- বর্তমান ব্যালেন্স = মোট জমা - মোট ক্রয় - মোট উত্তোলন")
    print("\nDisplay Rules:")
    print("- If balance < 0: Show as negative with '(বাকি)' - customer owes money")
    print("- If balance > 0: Show as positive with '(কাস্টমার পাবে)' - customer has credit")
    print("- If balance = 0: Show as 0")
    print("=" * 80)
    
    customers = Customer.objects.filter(is_deleted=False)
    total_customers = customers.count()
    fixed_count = 0
    error_count = 0
    
    for idx, customer in enumerate(customers, 1):
        print(f"\n[{idx}/{total_customers}] Processing: {customer.name} ({customer.mobile_number})")
        
        try:
            # Get old balance
            old_balance = customer.current_balance
            
            # Use the new recalculate_balance method
            correct_balance = customer.recalculate_balance()
            
            # Get transaction counts for reporting
            total_submissions = customer.transactions.filter(
                transaction_type='submission',
                is_reversed=False,
                is_deleted=False
            ).count()
            
            total_purchases = customer.transactions.filter(
                transaction_type='purchase',
                is_reversed=False,
                is_deleted=False
            ).exclude(status='cancelled').count()
            
            cancelled_purchases = customer.transactions.filter(
                transaction_type='purchase',
                status='cancelled',
                is_deleted=False
            ).count()
            
            reversed_transactions = customer.transactions.filter(
                is_reversed=True,
                is_deleted=False
            ).count()
            
            print(f"  📊 Transaction Summary:")
            print(f"     - Submissions: {total_submissions}")
            print(f"     - Active Purchases: {total_purchases}")
            print(f"     - Cancelled Purchases: {cancelled_purchases} (excluded from balance)")
            print(f"     - Reversed Transactions: {reversed_transactions} (excluded from balance)")
            
            print(f"  💰 Balance Calculation:")
            print(f"     - মোট জমা: ৳{customer.total_submitted:,.2f}")
            print(f"     - মোট ক্রয়: ৳{customer.total_purchased:,.2f}")
            print(f"     - মোট উত্তোলন: ৳{customer.total_withdrawn:,.2f}")
            
            if old_balance != correct_balance:
                print(f"  ❌ Balance mismatch detected!")
                print(f"     Old balance: ৳{old_balance:,.2f}")
                print(f"     Correct balance: ৳{correct_balance:,.2f}")
                print(f"     Difference: ৳{correct_balance - old_balance:,.2f}")
                
                # Save the corrected balance
                customer.save()
                
                # Display format
                if correct_balance < 0:
                    display = f"৳{correct_balance:,.2f} (বাকি)"
                elif correct_balance > 0:
                    display = f"৳{correct_balance:,.2f} (কাস্টমার পাবে)"
                else:
                    display = f"৳0.00"
                
                print(f"  ✅ Balance fixed! New display: {display}")
                fixed_count += 1
            else:
                # Display format
                if correct_balance < 0:
                    display = f"৳{correct_balance:,.2f} (বাকি)"
                elif correct_balance > 0:
                    display = f"৳{correct_balance:,.2f} (কাস্টমার পাবে)"
                else:
                    display = f"৳0.00"
                    
                print(f"  ✅ Balance is correct: {display}")
        
        except Exception as e:
            print(f"  ❌ Error processing customer: {str(e)}")
            error_count += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total customers processed: {total_customers}")
    print(f"Balances fixed: {fixed_count}")
    print(f"Balances already correct: {total_customers - fixed_count - error_count}")
    print(f"Errors: {error_count}")
    print("=" * 80)
    
    if fixed_count > 0:
        print(f"\n✅ Successfully fixed {fixed_count} customer balance(s)!")
    else:
        print("\n✅ All customer balances are already correct!")
    
    if error_count > 0:
        print(f"\n⚠️  {error_count} error(s) occurred during processing.")

if __name__ == '__main__':
    try:
        fix_customer_balances()
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
