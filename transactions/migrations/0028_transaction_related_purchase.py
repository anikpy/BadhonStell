# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0008_customer_deleted_at_customer_is_deleted_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='related_purchase',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='linked_payments', to='transactions.transaction', verbose_name='Related Purchase'),
        ),
    ]