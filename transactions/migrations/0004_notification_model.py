# Generated migration for Notification model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0003_transaction_payment_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('payment_due', 'Payment Due'), ('delivery_due', 'Delivery Due')], max_length=20, verbose_name='Notification Type')),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('message', models.TextField(verbose_name='Message')),
                ('is_read', models.BooleanField(default=False, verbose_name='Is Read')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='Read At')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='transactions.customer', verbose_name='Customer')),
                ('transaction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='transactions.transaction', verbose_name='Transaction')),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'ordering': ['-created_at'],
            },
        ),
    ]