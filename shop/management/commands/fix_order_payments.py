from django.core.management.base import BaseCommand
from shop.models import Order, OrderPayment
from decimal import Decimal
class Command(BaseCommand):
    help = 'Fix payment data for all orders'
    def handle(self, *args, **options):
        orders = Order.objects.all()
        fixed_count = 0
        for order in orders:
            total_from_payments = sum(
                Decimal(str(p.amount)) for p in order.payments.all()
            )
            correct_due = order.total_price - total_from_payments
            if (
                order.cash_paid != total_from_payments
                or order.due_amount != correct_due
            ):
                Order.objects.filter(pk=order.pk).update(
                    cash_paid=total_from_payments,
                    due_amount=correct_due,
                    initial_payment_migrated=True,
                )
                fixed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Order #{order.pk}: paid ৳{total_from_payments}, due ৳{correct_due}"
                    )
                )
        self.stdout.write(self.style.SUCCESS(f"\n✅ Fixed {fixed_count} orders!"))
