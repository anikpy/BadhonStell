"""
Management command to migrate all customer data from Custom Order (Order model) 
to Test Order (TestCustomerTransaction model) for the test customer system.
This preserves all real data while transitioning to the new system.
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum, Q
from decimal import Decimal
from shop.models import (
    Customer, Order, OrderItem, OrderPayment,
    TestCustomer, TestCustomerTransaction
)


class Command(BaseCommand):
    help = 'Migrate all customer data from Custom Order to Test Order system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it',
        )
        parser.add_argument(
            '--customer-id',
            type=int,
            help='Migrate only a specific customer by ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specific_customer_id = options.get('customer_id')

        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('MIGRATING CUSTOMER DATA TO TEST ORDER SYSTEM'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  DRY RUN MODE - No data will be modified\n'))

        # Get all customers with orders
        if specific_customer_id:
            customers = Customer.objects.filter(pk=specific_customer_id).annotate(
                order_count=Count('orders')
            ).filter(order_count__gt=0)
        else:
            customers = Customer.objects.annotate(
                order_count=Count('orders')
            ).filter(order_count__gt=0)

        total_customers = customers.count()
        self.stdout.write(f'\nFound {total_customers} customers with orders\n')

        if total_customers == 0:
            self.stdout.write(self.style.WARNING('No customers with orders found. Nothing to migrate.'))
            return

        migrated_customers = 0
        migrated_transactions = 0
        errors = []

        for customer in customers:
            try:
                self.stdout.write(f'\nProcessing: {customer.name} ({customer.mobile_number})')
                
                # Get all orders for this customer
                orders = Order.objects.filter(customer=customer).order_by('order_date', 'created_at')
                
                if not orders.exists():
                    self.stdout.write(f'  ⏭️  No orders found')
                    continue

                # Create or get TestCustomer
                if not dry_run:
                    test_customer, created = TestCustomer.objects.get_or_create(
                        mobile_number=customer.mobile_number,
                        defaults={
                            'name': customer.name,
                            'address': customer.address or '',
                            'current_balance': Decimal('0'),
                        }
                    )
                    if created:
                        self.stdout.write(f'  ✅ Created TestCustomer: {test_customer.name}')
                    else:
                        self.stdout.write(f'  ℹ️  Using existing TestCustomer: {test_customer.name}')
                else:
                    test_customer = None
                    self.stdout.write(f'  ℹ️  Would create/get TestCustomer: {customer.name}')

                # Calculate totals
                total_purchases = Decimal('0')
                total_payments = Decimal('0')

                # Process each order
                for order in orders:
                    self.stdout.write(f'  📦 Processing Order #{order.pk} - {order.order_date}')
                    
                    # Get order items
                    items = order.items.all()
                    if not items.exists():
                        self.stdout.write(f'    ⏭️  No items in order')
                        continue

                    # Calculate order total
                    order_total = sum(item.quantity * item.unit_price for item in items)
                    
                    # Apply order-level discount if any
                    if order.discount_percentage > 0:
                        discount_amount = (order_total * order.discount_percentage) / 100
                        order_total = order_total - discount_amount

                    # Create purchase transaction for this order
                    if not dry_run and test_customer:
                        # Create a combined item description
                        item_descriptions = []
                        for item in items:
                            item_descriptions.append(
                                f"{item.product_name} × {item.quantity} @ ৳{item.unit_price}"
                            )
                        
                        transaction = TestCustomerTransaction.objects.create(
                            customer=test_customer,
                            transaction_type='purchase',
                            amount=order_total,
                            item_name=f"Order #{order.pk} - {items.count()} items",
                            item_description=' | '.join(item_descriptions),
                            item_quantity=sum(item.quantity for item in items),
                            item_unit_price=order_total / sum(item.quantity for item in items) if sum(item.quantity for item in items) > 0 else Decimal('0'),
                            notes=f'Migrated from Order #{order.pk} | Date: {order.order_date}',
                            status='completed',
                            created_by=None  # No user context in management command
                        )
                        
                        # Update stock for inventory products
                        for item in items:
                            try:
                                from shop.models import InventoryProduct
                                inventory_product = InventoryProduct.objects.filter(
                                    name__iexact=item.product_name
                                ).first()
                                if inventory_product:
                                    # Don't deduct stock again since it was already deducted
                                    # Just record the transaction
                                    pass
                            except:
                                pass

                        self.stdout.write(
                            self.style.SUCCESS(f'    ✅ Created purchase transaction: {transaction.transaction_number} - ৳{order_total}')
                        )
                        migrated_transactions += 1
                    else:
                        self.stdout.write(f'    ℹ️  Would create purchase transaction: ৳{order_total}')

                    total_purchases += order_total

                    # Process payments for this order
                    payments = order.payments.all()
                    for payment in payments:
                        if not dry_run and test_customer:
                            # Create submission transaction for payment
                            transaction = TestCustomerTransaction.objects.create(
                                customer=test_customer,
                                transaction_type='submission',
                                amount=payment.amount,
                                notes=f'Migrated from Order #{order.pk} payment | Date: {payment.payment_date}',
                                status='completed',
                                created_by=None
                            )
                            self.stdout.write(
                                self.style.SUCCESS(f'    💰 Created payment transaction: {transaction.transaction_number} - ৳{payment.amount}')
                            )
                            migrated_transactions += 1
                        else:
                            self.stdout.write(f'    ℹ️  Would create payment transaction: ৳{payment.amount}')
                        
                        total_payments += payment.amount

                # Update customer balance
                if not dry_run and test_customer:
                    # Calculate final balance: total submissions - total purchases
                    final_balance = total_payments - total_purchases
                    test_customer.current_balance = final_balance
                    test_customer.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'  💳 Updated balance: ৳{final_balance} (Purchases: ৳{total_purchases}, Payments: ৳{total_payments})')
                    )
                else:
                    self.stdout.write(
                        f'  ℹ️  Would update balance: ৳{total_payments - total_purchases}'
                    )

                migrated_customers += 1

            except Exception as e:
                error_msg = f'Error processing customer {customer.name}: {str(e)}'
                errors.append(error_msg)
                self.stdout.write(self.style.ERROR(f'  ❌ {error_msg}'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 80))
        self.stdout.write(self.style.SUCCESS('MIGRATION SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(f'Customers processed: {migrated_customers}/{total_customers}')
        self.stdout.write(f'Transactions created: {migrated_transactions}')
        
        if errors:
            self.stdout.write(self.style.ERROR(f'\n❌ Errors encountered: {len(errors)}'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'  - {error}'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Migration completed successfully!'))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  This was a DRY RUN. No data was modified.'))
            self.stdout.write(self.style.WARNING('Run without --dry-run to perform the actual migration.\n'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Data has been migrated to Test Order system.'))
            self.stdout.write(self.style.SUCCESS('You can now access test customers at: /admin-panel/test-customers/\n'))