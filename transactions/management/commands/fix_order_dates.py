from django.core.management.base import BaseCommand
from transactions.models import Transaction
from django.utils import timezone


class Command(BaseCommand):
    help = 'Fix order_date by using created_at date for all transactions'

    def handle(self, *args, **options):
        """Fix order_date values based on created_at timestamps"""
        
        # Get all transactions
        transactions = Transaction.objects.all()
        
        updated_count = 0
        
        for txn in transactions:
            # Extract date from created_at and set it as order_date
            if txn.created_at:
                actual_date = txn.created_at.date()
                
                # Only update if order_date is different from actual date
                if txn.order_date != actual_date:
                    txn.order_date = actual_date
                    txn.save(update_fields=['order_date'])
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Updated {txn.transaction_number}: {txn.order_date}'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully updated {updated_count} transactions with correct order dates!'
            )
        )
