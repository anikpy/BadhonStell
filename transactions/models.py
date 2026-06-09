from django.db import models
from django.utils import timezone
from decimal import Decimal


class Customer(models.Model):
    """Customer model for transaction system"""
    name = models.CharField(max_length=200, verbose_name='Customer Name')
    mobile_number = models.CharField(max_length=20, unique=True, verbose_name='Mobile Number')
    address = models.TextField(verbose_name='Address', blank=True)
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Current Balance', default=0)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    is_deleted = models.BooleanField(default=False, verbose_name='Is Deleted')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Deleted At')

    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.mobile_number}"

    @property
    def total_submitted(self):
        from django.db.models import Sum
        result = self.transactions.filter(
            transaction_type='submission',
            is_reversed=False
        ).aggregate(total=Sum('amount'))
        return result['total'] or 0

    @property
    def total_purchased(self):
        from django.db.models import Sum
        result = self.transactions.filter(
            transaction_type='purchase',
            is_reversed=False
        ).aggregate(total=Sum('amount'))
        return abs(result['total'] or 0)

    @property
    def total_withdrawn(self):
        from django.db.models import Sum
        result = self.transactions.filter(
            transaction_type='withdrawal',
            is_reversed=False
        ).aggregate(total=Sum('amount'))
        return abs(result['total'] or 0)


class Transaction(models.Model):
    """Transaction model - unified model for all transaction types"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('submission', 'Submission (Deposit)'),
        ('purchase', 'Purchase'),
        ('withdrawal', 'Withdrawal'),
        ('adjustment', 'Adjustment'),
        ('reversal', 'Reversal'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'চলমান'),
        ('ready', 'প্রস্তুত'),
        ('completed', 'সম্পন্ন'),
        ('cancelled', 'বাতিল'),
    ]
    
    DELIVERY_STATUS_CHOICES = [
        ('not_delivered', 'ডেলিভারি হয়নি'),
        ('delivered', 'ডেলিভারি সম্পন্ন'),
    ]
    
    # Edit tracking
    is_edited = models.BooleanField(default=False, verbose_name='Is Edited')
    original_transaction = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                             related_name='edited_versions', verbose_name='Original Transaction')
    
    # Core fields
    transaction_number = models.CharField(max_length=50, unique=True, verbose_name='Transaction Number', editable=False)
    customer = models.ForeignKey('Customer', on_delete=models.PROTECT, related_name='transactions', verbose_name='Customer')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, verbose_name='Transaction Type')
    
    # Financial tracking
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Amount')
    balance_before = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Balance Before', default=0)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Balance After', default=0)
    
    # Item details (for purchase type - single item for backward compatibility)
    item_name = models.CharField(max_length=200, verbose_name='Item Name', blank=True)
    item_description = models.TextField(verbose_name='Item Description', blank=True)
    item_quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Quantity', null=True, blank=True)
    item_unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Unit Price', null=True, blank=True)
    inventory_product = models.ForeignKey('shop.InventoryProduct', on_delete=models.SET_NULL, null=True, blank=True, 
                                          verbose_name='Inventory Product')
    
    # Discount tracking
    item_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Item Discount (%)')
    item_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Item Discount Amount')
    total_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Total Discount (%)')
    total_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Total Discount Amount')
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Gross Amount')
    
    # Status and audit
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Order Status')
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='not_delivered', verbose_name='Delivery Status')
    notes = models.TextField(verbose_name='Notes', blank=True)
    
    # Date tracking
    order_date = models.DateField(default=timezone.now, verbose_name='Order Date')
    delivery_date = models.DateField(null=True, blank=True, verbose_name='Delivery Date')
    payment_date = models.DateField(null=True, blank=True, verbose_name='Payment Due Date')
    
    # Reversal tracking
    reverses_transaction = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                             related_name='reversed_by_transactions', verbose_name='Reversed Transaction')
    is_reversed = models.BooleanField(default=False, verbose_name='Is Reversed')
    
    # Staff tracking
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Created By')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    is_deleted = models.BooleanField(default=False, verbose_name='Is Deleted')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='Deleted At')
    
    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', '-created_at']),
            models.Index(fields=['transaction_type', 'status']),
            models.Index(fields=['transaction_number']),
        ]
    
    def __str__(self):
        return f"{self.transaction_number} - {self.get_transaction_type_display()} - ৳{self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_number:
            from django.utils import timezone
            year = timezone.now().year
            last_txn = Transaction.objects.filter(
                transaction_number__startswith=f'TXN-{year}'
            ).order_by('-transaction_number').first()
            
            if last_txn and last_txn.transaction_number:
                try:
                    last_num = int(last_txn.transaction_number.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            self.transaction_number = f"TXN-{year}-{new_num:05d}"
        
        # Always recalculate balance from current customer balance
        self.balance_before = self.customer.current_balance
        
        if self.transaction_type == 'submission':
            self.balance_after = self.balance_before + self.amount
        elif self.transaction_type in ['purchase', 'withdrawal']:
            self.balance_after = self.balance_before - abs(self.amount)
        elif self.transaction_type == 'adjustment':
            self.balance_after = self.balance_before + self.amount
        elif self.transaction_type == 'reversal':
            # For reversal, reverse the original transaction's effect
            if self.reverses_transaction:
                # If reversing a reversal, we need to reverse the reversal's effect
                if self.reverses_transaction.transaction_type == 'reversal':
                    # Reversing a reversal means undoing the reversal
                    # So we apply the same logic as the original reversal but in opposite direction
                    if self.reverses_transaction.reverses_transaction:
                        original_txn = self.reverses_transaction.reverses_transaction
                        if original_txn.transaction_type == 'submission':
                            # Original was submission, reversal subtracted it, so we add it back
                            self.balance_after = self.balance_before + abs(original_txn.amount)
                        else:
                            # Original was purchase/withdrawal, reversal added it, so we subtract it back
                            self.balance_after = self.balance_before - abs(original_txn.amount)
                    else:
                        self.balance_after = self.balance_before + self.amount
                elif self.reverses_transaction.transaction_type == 'submission':
                    self.balance_after = self.balance_before - abs(self.reverses_transaction.amount)
                else:
                    self.balance_after = self.balance_before + abs(self.reverses_transaction.amount)
            else:
                self.balance_after = self.balance_before + self.amount
        
        super().save(*args, **kwargs)
        
        # Update customer balance for all non-reversed orders (pending, ready, completed)
        if not self.is_reversed:
            self.customer.current_balance = self.balance_after
            self.customer.save()


class TransactionItem(models.Model):
    """Transaction Item - multiple items in a transaction"""
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='items', verbose_name='Transaction')
    product_name = models.CharField(max_length=200, verbose_name='Product Name')
    product_description = models.TextField(verbose_name='Product Description', blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Quantity')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Unit Price')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Discount (%)')
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Discount Amount', editable=False)
    gross_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Gross Amount', editable=False)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Net Amount', editable=False)
    inventory_product = models.ForeignKey('shop.InventoryProduct', on_delete=models.SET_NULL, null=True, blank=True, 
                                          verbose_name='Inventory Product')
    
    class Meta:
        verbose_name = 'Transaction Item'
        verbose_name_plural = 'Transaction Items'
    
    def save(self, *args, **kwargs):
        self.gross_amount = self.quantity * self.unit_price
        self.discount_amount = (self.gross_amount * self.discount_percentage) / 100
        self.net_amount = self.gross_amount - self.discount_amount
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product_name} × {self.quantity} - {self.transaction.transaction_number}"


class TransactionHistory(models.Model):
    """Transaction History - tracking all actions"""
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('edited', 'Edited'),
        ('reversed', 'Reversed'),
        ('deleted', 'Deleted'),
    ]
    
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='history', verbose_name='Transaction')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='Action')
    old_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Old Amount')
    new_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='New Amount')
    old_balance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Old Balance')
    new_balance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='New Balance')
    notes = models.TextField(verbose_name='Notes', blank=True)
    performed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Performed By')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    
    class Meta:
        verbose_name = 'Transaction History'
        verbose_name_plural = 'Transaction Histories'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction.transaction_number} - {self.get_action_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


# ==================== DEPRECATED MODELS (Keep for backward compatibility) ====================

class CustomerSubmission(models.Model):
    """DEPRECATED - Use Transaction instead"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='submissions', verbose_name='Customer')
    submitted_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Submitted Amount')
    notes = models.TextField(verbose_name='Notes', blank=True)
    submission_date = models.DateTimeField(auto_now_add=True, verbose_name='Submission Date')

    class Meta:
        verbose_name = 'Customer Submission (Deprecated)'
        verbose_name_plural = 'Customer Submissions (Deprecated)'
        ordering = ['-submission_date']

    def __str__(self):
        return f"{self.customer.name} - ৳{self.submitted_amount}"

    @property
    def remaining_amount(self):
        """Remaining amount = submission - expenses"""
        total_spent = sum(item.total_price for item in self.items.all())
        return self.submitted_amount - total_spent


class CustomerItem(models.Model):
    """DEPRECATED - Use TransactionItem instead"""
    submission = models.ForeignKey(CustomerSubmission, on_delete=models.CASCADE, related_name='items', verbose_name='Submission')
    product_name = models.CharField(max_length=200, verbose_name='Product Name')
    product_description = models.TextField(verbose_name='Product Description', blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Quantity', default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Unit Price')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total Price', editable=False)
    added_date = models.DateTimeField(auto_now_add=True, verbose_name='Added Date')

    class Meta:
        verbose_name = 'Customer Item (Deprecated)'
        verbose_name_plural = 'Customer Items (Deprecated)'

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} × {self.quantity} - {self.submission.customer.name}"


class CustomerNote(models.Model):
    """Customer notes - for storing small notes about customers"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='notes', verbose_name='Customer')
    note = models.TextField(verbose_name='Note')
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Created By')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    is_dismissed_from_dashboard = models.BooleanField(default=False, verbose_name='Dismissed from Dashboard')

    class Meta:
        verbose_name = 'Customer Note'
        verbose_name_plural = 'Customer Notes'
        ordering = ['-created_at']

    def __str__(self):
        return f"Note for {self.customer.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
