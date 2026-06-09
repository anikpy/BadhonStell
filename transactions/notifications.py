"""
Notification utilities for payment due alerts
"""
from django.utils import timezone
from datetime import date
from .models import Notification, Transaction


def generate_payment_notifications():
    """
    Generate notifications for transactions with payment dates that are TODAY or OVERDUE
    Only for purchase transactions
    """
    today = date.today()
    
    # Find all purchase transactions with payment_date <= today and not reversed
    transactions = Transaction.objects.filter(
        transaction_type='purchase',
        status='completed',
        is_reversed=False,
        payment_date__isnull=False,
        payment_date__lte=today
    ).select_related('customer')
    
    created_count = 0
    
    for transaction in transactions:
        # Check if notification already exists for this transaction
        existing_notification = Notification.objects.filter(
            transaction=transaction,
            notification_type='payment_due',
            is_read=False
        ).exists()
        
        if not existing_notification:
            # Create notification
            if transaction.payment_date == today:
                title = f"💰 Payment Due Today: {transaction.customer.name}"
                message = f"Payment is due today for order {transaction.transaction_number}. Amount: ৳{transaction.amount}"
            else:
                days_overdue = (today - transaction.payment_date).days
                title = f"⚠️ Payment Overdue: {transaction.customer.name}"
                message = f"Payment is {days_overdue} days overdue for order {transaction.transaction_number}. Amount: ৳{transaction.amount}"
            
            Notification.objects.create(
                notification_type='payment_due',
                customer=transaction.customer,
                transaction=transaction,
                title=title,
                message=message,
                is_read=False
            )
            created_count += 1
    
    return created_count


def get_unread_notifications():
    """Get all unread notifications"""
    return Notification.objects.filter(is_read=False).order_by('-created_at')


def get_customer_unread_notifications(customer):
    """Get unread notifications for a specific customer"""
    return customer.notifications.filter(is_read=False).order_by('-created_at')


def get_unread_notification_count():
    """Get count of unread notifications"""
    return Notification.objects.filter(is_read=False).count()


def get_customer_unread_notification_count(customer):
    """Get count of unread notifications for a customer"""
    return customer.notifications.filter(is_read=False).count()