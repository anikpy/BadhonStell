"""
Management command to import customers and their orders from custom order system to test order system
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from shop.models import (
    Customer, Order, OrderItem,
    TestCustomer, TestCustomerTransaction, TestCustomerTransactionItem, TestTransactionHistory
)


class Command(BaseCommand):
    help = 'Import customers and their orders from custom order system to test order system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--customer-id',
            type=int,
            help='Import specific customer by ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        customer_id = options.get('customer_id')

        if customer_id:
            # Import specific customer
            try:
                customer = Customer.objects.get(pk=customer_id)
                self.import_customer(customer, dry_run)
            except Customer.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Customer with ID {customer_id} not found'))
        else:
            # Import all customers
            customers = Customer.objects.all()
            total_customers = customers.count()
            
            self.stdout.write(f'Found {total_customers} customers to import')
            
            if dry_run:
                self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be imported'))
            
            imported_count = 0
            skipped_count = 0
            
            for customer in customers:
                try:
                    if self.import_customer(customer, dry_run):
                        imported_count += 1
                    else:
                        skipped_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error importing customer {customer.name}: {str(e)}'))
                    skipped_count += 1
            
            self.stdout.write(self.style.SUCCESS(
                f'\nImport completed: {imported_count} customers imported, {skipped_count} skipped'
            ))

    def import_customer(self, customer, dry_run=False):
        """Import a single customer and their orders"""
        # Check if test customer already exists
        existing_test_customer = TestCustomer.objects.filter(
            mobile_number=customer.mobile_number
        ).first()
        
        if existing_test_customer:
            self.stdout.write(
                self.style.WARNING(f'  ⊙ {customer.name} (Mobile: {customer.mobile_number}) - Already exists, skipping')
            )
            return False
        
        self.stdout.write(f'  → Importing {customer.name} (Mobile: {customer.mobile_number})')
        
        if dry_run:
            # Count orders
            order_count = customer.orders.count()
            self.stdout.write(f'    Would create: 1 test customer + {order_count} purchase transactions')
            return True
        
        # Create test customer
        test_customer = TestCustomer.objects.create(
            name=customer.name,
            mobile_number=customer.mobile_number,
            address=customer.address or '',
            current_balance=Decimal('0')
        )
        
        self.stdout.write(f'    ✓ Created test customer (ID: {test_customer.pk})')
        
        # Import all orders as purchase transactions
        orders = customer.orders.all().order_by('created_at')
        imported_orders = 0
        
        for order in orders:
            try:
                self.import_order_as_purchase(order, test_customer)
                imported_orders += 1
                
                # If order has cash_paid, create a submission transaction
                if order.cash_paid and order.cash_paid > 0:
                    self.import_order_payment_as_submission(order, test_customer)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'    ✗ Error importing order #{order.pk}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'    ✓ Imported {imported_orders}/{orders.count()} orders')
        )
        
        return True

    def import_order_as_purchase(self, order, test_customer):
        """Import a custom order as a test purchase transaction"""
        # Get all order items
        order_items = order.items.all()
        
        if not order_items.exists():
            self.stdout.write(
                self.style.WARNING(f'    ⊙ Order #{order.pk} has no items, skipping')
            )
            return
        
        # Calculate totals
        subtotal = sum(item.quantity * item.unit_price for item in order_items)
        
        # Create transaction items data
        items_data = []
        for item in order_items:
            items_data.append({
                'product_name': item.product_name,
                'product_description': item.product_description or '',
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'discount_percentage': item.discount_percentage or Decimal('0'),
            })
        
        # Calculate discount
        total_discount = order.discount_percentage or Decimal('0')
        discount_amount = (subtotal * total_discount) / 100
        final_total = subtotal - discount_amount
        
        # Create main transaction
        item_names = ', '.join([item.product_name for item in order_items])
        transaction = TestCustomerTransaction.objects.create(
            customer=test_customer,
            transaction_type='purchase',
            amount=final_total,
            item_name=item_names,
            item_description=f'{order_items.count()} items from order #{order.pk}',
            item_quantity=sum(item.quantity for item in order_items),
            item_unit_price=final_total / sum(item.quantity for item in order_items) if sum(item.quantity for item in order_items) > 0 else Decimal('0'),
            gross_amount=subtotal,
            item_discount_percentage=total_discount,
            item_discount_amount=discount_amount,
            total_discount_percentage=total_discount,
            total_discount_amount=discount_amount,
            notes=f'Imported from custom order #{order.pk}',
            status='completed',
            created_by=None  # System import
        )
        
        # Create transaction items
        for item_data in items_data:
            TestCustomerTransactionItem.objects.create(
                transaction=transaction,
                product_name=item_data['product_name'],
                product_description=item_data['product_description'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                discount_percentage=item_data['discount_percentage'],
                discount_amount=(item_data['quantity'] * item_data['unit_price'] * item_data['discount_percentage']) / 100,
                gross_amount=item_data['quantity'] * item_data['unit_price'],
                net_amount=item_data['quantity'] * item_data['unit_price'] * (Decimal('100') - item_data['discount_percentage']) / 100,
                inventory_product=None  # No inventory product reference for imported orders
            )
        
        # Create history record
        TestTransactionHistory.objects.create(
            transaction=transaction,
            action='created',
            old_balance=transaction.balance_before,
            new_balance=transaction.balance_after,
            notes=f'Imported from custom order #{order.pk}',
            performed_by=None
        )
        
        return True
    
    def import_order_payment_as_submission(self, order, test_customer):
        """Import order payment as a submission transaction"""
        payment_amount = order.cash_paid
        
        if not payment_amount or payment_amount <= 0:
            return
        
        # Create submission transaction for the payment
        transaction = TestCustomerTransaction.objects.create(
            customer=test_customer,
            transaction_type='submission',
            amount=payment_amount,
            item_name=f'অর্ডার #{order.pk} এর পেমেন্ট',
            item_description=f'Payment for order #{order.pk}',
            item_quantity=1,
            item_unit_price=payment_amount,
            notes=f'Imported payment from custom order #{order.pk}',
            status='completed',
            created_by=None  # System import
        )
        
        # Create history record
        TestTransactionHistory.objects.create(
            transaction=transaction,
            action='created',
            old_balance=transaction.balance_before,
            new_balance=transaction.balance_after,
            notes=f'Imported payment from custom order #{order.pk}',
            performed_by=None
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'    ✓ Imported payment: ৳{payment_amount} as submission')
        )
