from django.core.management.base import BaseCommand
from shop.models import Order

class Command(BaseCommand):
    help = 'Recompute Order.cash_paid and Order.due_amount from OrderPayment records'

    def handle(self, *args, **options):
        orders = Order.objects.all()
        count = 0
        for order in orders:
            total_paid = sum(p.amount for p in order.payments.all())
            order.cash_paid = total_paid
            order.due_amount = order.total_price - total_paid
            order.save()
            count += 1
        self.stdout.write(self.style.SUCCESS(f'Recomputed totals for {count} orders'))

