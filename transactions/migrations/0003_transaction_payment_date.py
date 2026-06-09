# Generated migration for adding payment_date field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0002_transaction_delivery_status_alter_transaction_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='payment_date',
            field=models.DateField(blank=True, null=True, verbose_name='Payment Due Date'),
        ),
        migrations.RunPython(
            code=lambda apps, schema_editor: backfill_payment_dates(apps, schema_editor),
            reverse_code=lambda apps, schema_editor: None,
        ),
    ]


def backfill_payment_dates(apps, schema_editor):
    """Backfill payment_date with delivery_date for existing transactions"""
    Transaction = apps.get_model('transactions', 'Transaction')
    
    # Update all transactions where payment_date is NULL and delivery_date is not NULL
    transactions_to_update = Transaction.objects.filter(
        payment_date__isnull=True,
        delivery_date__isnull=False
    )
    
    for txn in transactions_to_update:
        txn.payment_date = txn.delivery_date
        txn.save()
    
    print(f"✓ Backfilled {transactions_to_update.count()} transactions with payment_date = delivery_date")