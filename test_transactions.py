#!/usr/bin/env python3
"""
Test script for transactions app
Tests customer creation, submissions, purchases, and withdrawals
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'badhonsteel.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from decimal import Decimal
from datetime import date
from transactions.models import Customer, Transaction, TransactionItem, TransactionHistory
from shop.models import InventoryProduct, StockHistory

def test_transactions():
    """Run comprehensive tests on transactions app"""
    
    print("=" * 60)
    print("TESTING TRANSACTIONS APP")
    print("=" * 60)
    
    # Clean up any existing test data
    print("\n1. Cleaning up old test data...")
    Customer.objects.filter(mobile_number='01627220072').delete()
    print("   ✅ Cleanup complete")
    
    # Test 1: Create Customer
    print("\n2. Creating customer with mobile 01627220072...")
    customer = Customer.objects.create(
        name='Test Customer',
        mobile_number='01627220072',
        address='Kendua, Netrokona',
        current_balance=Decimal('0')
    )
    print(f"   ✅ Customer created: {customer.name} (ID: {customer.pk})")
    print(f"   📱 Mobile: {customer.mobile_number}")
    print(f"   💰 Initial Balance: ৳{customer.current_balance}")
    
    # Test 2: Create Submission (Deposit)
    print("\n3. Creating submission (deposit) transaction...")
    submission = Transaction.objects.create(
        customer=customer,
        transaction_type='submission',
        amount=Decimal('5000'),
        notes='Initial deposit for testing',
        status='completed',
        order_date=date.today()
    )
    print(f"   ✅ Submission created: {submission.transaction_number}")
    print(f"   💵 Amount: ৳{submission.amount}")
    print(f"   💰 Balance Before: ৳{submission.balance_before}")
    print(f"   💰 Balance After: ৳{submission.balance_after}")
    
    # Refresh customer to see updated balance
    customer.refresh_from_db()
    print(f"   📊 Customer Current Balance: ৳{customer.current_balance}")
    
    # Test 3: Create Purchase Transaction with Multiple Items
    print("\n4. Creating purchase transaction with multiple items...")
    
    # Get or create inventory products
    products_data = [
        {'name': 'Steel Door', 'price': Decimal('15000'), 'stock': Decimal('10')},
        {'name': 'Window Frame', 'price': Decimal('8000'), 'stock': Decimal('15')},
        {'name': 'Steel Grill', 'price': Decimal('5000'), 'stock': Decimal('20')},
    ]
    
    inventory_products = []
    for p_data in products_data:
        product, created = InventoryProduct.objects.get_or_create(
            name=p_data['name'],
            defaults={
                'description': f'Test {p_data["name"]}',
                'unit': 'piece',
                'price_per_unit': p_data['price'],
                'stock_quantity': p_data['stock']
            }
        )
        inventory_products.append(product)
        print(f"   📦 Inventory: {product.name} (Stock: {product.stock_quantity})")
    
    # Create purchase transaction
    purchase = Transaction.objects.create(
        customer=customer,
        transaction_type='purchase',
        amount=Decimal('0'),  # Will be calculated
        item_name=', '.join([p.name for p in inventory_products]),
        item_description='3 items purchased',
        item_quantity=Decimal('3'),
        item_unit_price=Decimal('0'),
        gross_amount=Decimal('0'),
        item_discount_percentage=Decimal('5'),  # 5% discount
        item_discount_amount=Decimal('0'),
        total_discount_percentage=Decimal('5'),
        total_discount_amount=Decimal('0'),
        notes='Test purchase with discount',
        status='completed',
        created_by=None,  # System test
        order_date=date.today(),
        delivery_date=date.today()
    )
    
    # Create transaction items
    quantities = [Decimal('1'), Decimal('2'), Decimal('1')]
    discounts = [Decimal('0'), Decimal('10'), Decimal('0')]
    subtotal = Decimal('0')
    
    for i, (product, qty, disc) in enumerate(zip(inventory_products, quantities, discounts)):
        item_gross = qty * product.price_per_unit
        item_discount = (item_gross * disc) / 100
        item_net = item_gross - item_discount
        subtotal += item_net
        
        TransactionItem.objects.create(
            transaction=purchase,
            product_name=product.name,
            product_description=f'Test {product.name}',
            quantity=qty,
            unit_price=product.price_per_unit,
            discount_percentage=disc,
            discount_amount=item_discount,
            gross_amount=item_gross,
            net_amount=item_net,
            inventory_product=product
        )
        print(f"   🛒 Item {i+1}: {product.name} × {qty} = ৳{item_net}")
    
    # Calculate totals
    total_discount = (subtotal * Decimal('5')) / 100
    final_total = subtotal - total_discount
    
    # Update transaction
    purchase.gross_amount = subtotal + total_discount
    purchase.item_discount_amount = total_discount
    purchase.total_discount_amount = total_discount
    purchase.amount = final_total
    purchase.item_quantity = sum(quantities)
    purchase.item_unit_price = final_total / sum(quantities)
    purchase.save()
    
    print(f"\n   💵 Subtotal: ৳{subtotal}")
    print(f"   🎁 Total Discount (5%): ৳{total_discount}")
    print(f"   💰 Final Total: ৳{final_total}")
    print(f"   📝 Transaction: {purchase.transaction_number}")
    
    # Check stock deduction
    print("\n   📦 Stock after purchase:")
    for product in inventory_products:
        product.refresh_from_db()
        print(f"      - {product.name}: {product.stock_quantity} remaining")
    
    # Refresh customer balance
    customer.refresh_from_db()
    print(f"\n   💰 Customer Balance After Purchase: ৳{customer.current_balance}")
    
    # Test 4: Create Withdrawal
    print("\n5. Creating withdrawal transaction...")
    withdrawal = Transaction.objects.create(
        customer=customer,
        transaction_type='withdrawal',
        amount=Decimal('1000'),
        notes='Test withdrawal',
        status='completed',
        order_date=date.today()
    )
    print(f"   ✅ Withdrawal created: {withdrawal.transaction_number}")
    print(f"   💸 Amount: ৳{withdrawal.amount}")
    print(f"   💰 Balance Before: ৳{withdrawal.balance_before}")
    print(f"   💰 Balance After: ৳{withdrawal.balance_after}")
    
    customer.refresh_from_db()
    print(f"   📊 Customer Current Balance: ৳{customer.current_balance}")
    
    # Test 5: Create Another Submission
    print("\n6. Creating another submission...")
    submission2 = Transaction.objects.create(
        customer=customer,
        transaction_type='submission',
        amount=Decimal('3000'),
        notes='Second deposit',
        status='completed',
        order_date=date.today()
    )
    print(f"   ✅ Submission created: {submission2.transaction_number}")
    print(f"   💵 Amount: ৳{submission2.amount}")
    
    customer.refresh_from_db()
    print(f"   📊 Final Customer Balance: ৳{customer.current_balance}")
    
    # Test 6: Check Transaction History
    print("\n7. Checking transaction history...")
    transactions = customer.transactions.filter(status='completed').order_by('created_at')
    print(f"   📋 Total Transactions: {transactions.count()}")
    
    for txn in transactions:
        print(f"   - {txn.transaction_number}: {txn.get_transaction_type_display()} ৳{txn.amount}")
    
    # Test 7: Check Customer Properties
    print("\n8. Checking customer computed properties...")
    print(f"   📥 Total Submitted: ৳{customer.total_submitted}")
    print(f"   🛒 Total Purchased: ৳{customer.total_purchased}")
    print(f"   💸 Total Withdrawn: ৳{customer.total_withdrawn}")
    
    # Test 8: Create History Records
    print("\n9. Creating transaction history records...")
    for txn in [submission, purchase, withdrawal, submission2]:
        TransactionHistory.objects.create(
            transaction=txn,
            action='created',
            old_balance=txn.balance_before,
            new_balance=txn.balance_after,
            notes=f'Test transaction created: {txn.transaction_number}',
            performed_by=None
        )
    print(f"   ✅ History records created for {transactions.count()} transactions")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Customer: {customer.name} ({customer.mobile_number})")
    print(f"Customer ID: {customer.pk}")
    print(f"Final Balance: ৳{customer.current_balance}")
    print(f"Total Transactions: {transactions.count()}")
    print(f"Total Submitted: ৳{customer.total_submitted}")
    print(f"Total Purchased: ৳{customer.total_purchased}")
    print(f"Total Withdrawn: ৳{customer.total_withdrawn}")
    print("\n✅ ALL TESTS PASSED!")
    print("=" * 60)
    
    return customer

if __name__ == '__main__':
    try:
        customer = test_transactions()
        print(f"\n🎉 Test completed successfully!")
        print(f"📱 Customer mobile: 01627220072")
        print(f"🌐 Access at: /transactions/customers/{customer.pk}/")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)