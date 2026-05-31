from django.core.management.base import BaseCommand
from shop.models import Customer, CustomerDeposit
from decimal import Decimal


class Command(BaseCommand):
    help = 'Fix deposit balance inconsistencies for all customers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--customer-id',
            type=int,
            help='Fix balance for a specific customer ID',
        )

    def handle(self, *args, **options):
        customer_id = options.get('customer_id')
        
        if customer_id:
            customers = Customer.objects.filter(pk=customer_id)
        else:
            customers = Customer.objects.all()
        
        fixed_count = 0
        
        for customer in customers:
            # Calculate correct balance from deposits
            total_deposits = sum(
                d.amount for d in customer.deposits.filter(transaction_type='deposit')
            ) or Decimal('0')
            total_deductions = sum(
                d.amount for d in customer.deposits.filter(transaction_type='deduct')
            ) or Decimal('0')
            correct_balance = total_deposits - total_deductions
            
            # Check if balance is incorrect
            if customer.deposit_balance != correct_balance:
                old_balance = customer.deposit_balance
                customer.deposit_balance = correct_balance
                customer.save()
                
                self.stdout.write(
                    self.style.WARNING(
                        f'Fixed {customer.name}: {old_balance} → {correct_balance}'
                    )
                )
                fixed_count += 1
        
        if fixed_count == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ All customer deposit balances are correct!')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Fixed {fixed_count} customer(s)!')
            )
