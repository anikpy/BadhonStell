# Generated initial migration for transactions app

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Customer Name')),
                ('mobile_number', models.CharField(max_length=20, unique=True, verbose_name='Mobile Number')),
                ('address', models.TextField(blank=True, verbose_name='Address')),
                ('current_balance', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Current Balance')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'Customer',
                'verbose_name_plural': 'Customers',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_number', models.CharField(editable=False, max_length=50, unique=True, verbose_name='Transaction Number')),
                ('transaction_type', models.CharField(choices=[('submission', 'Submission (Deposit)'), ('purchase', 'Purchase'), ('withdrawal', 'Withdrawal'), ('adjustment', 'Adjustment'), ('reversal', 'Reversal')], max_length=20, verbose_name='Transaction Type')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Amount')),
                ('balance_before', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Balance Before')),
                ('balance_after', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Balance After')),
                ('item_name', models.CharField(blank=True, max_length=200, verbose_name='Item Name')),
                ('item_description', models.TextField(blank=True, verbose_name='Item Description')),
                ('item_quantity', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Quantity')),
                ('item_unit_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Unit Price')),
                ('item_discount_percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Item Discount (%)')),
                ('item_discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Item Discount Amount')),
                ('total_discount_percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Total Discount (%)')),
                ('total_discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Total Discount Amount')),
                ('gross_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Gross Amount')),
                ('status', models.CharField(choices=[('pending', 'চলমান'), ('ready', 'প্রস্তুত'), ('completed', 'সম্পন্ন'), ('cancelled', 'বাতিল')], default='pending', max_length=20, verbose_name='Order Status')),
                ('delivery_status', models.CharField(choices=[('not_delivered', 'ডেলিভারি হয়নি'), ('delivered', 'ডেলিভারি সম্পন্ন')], default='not_delivered', max_length=20, verbose_name='Delivery Status')),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('order_date', models.DateField(default=django.utils.timezone.now, verbose_name='Order Date')),
                ('delivery_date', models.DateField(blank=True, null=True, verbose_name='Delivery Date')),
                ('payment_date', models.DateField(blank=True, null=True, verbose_name='Payment Due Date')),
                ('is_reversed', models.BooleanField(default=False, verbose_name='Is Reversed')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transactions', to='transactions.customer', verbose_name='Customer')),
            ],
            options={
                'verbose_name': 'Transaction',
                'verbose_name_plural': 'Transactions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TransactionItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=200, verbose_name='Product Name')),
                ('product_description', models.TextField(blank=True, verbose_name='Product Description')),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Quantity')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Unit Price')),
                ('discount_percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Discount (%)')),
                ('discount_amount', models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=10, verbose_name='Discount Amount')),
                ('gross_amount', models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=10, verbose_name='Gross Amount')),
                ('net_amount', models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=10, verbose_name='Net Amount')),
                ('inventory_product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='shop.inventoryproduct', verbose_name='Inventory Product')),
                ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='transactions.transaction', verbose_name='Transaction')),
            ],
            options={
                'verbose_name': 'Transaction Item',
                'verbose_name_plural': 'Transaction Items',
            },
        ),
        migrations.CreateModel(
            name='TransactionHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('created', 'Created'), ('edited', 'Edited'), ('reversed', 'Reversed'), ('deleted', 'Deleted')], max_length=20, verbose_name='Action')),
                ('old_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Old Amount')),
                ('new_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='New Amount')),
                ('old_balance', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Old Balance')),
                ('new_balance', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='New Balance')),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('performed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Performed By')),
                ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='transactions.transaction', verbose_name='Transaction')),
            ],
            options={
                'verbose_name': 'Transaction History',
                'verbose_name_plural': 'Transaction Histories',
                'ordering': ['-created_at'],
            },
        ),
    ]
