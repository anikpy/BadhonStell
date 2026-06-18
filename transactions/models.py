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
        """Total deposits (জমা) - only non-reversed submissions and non-deleted"""
        from django.db.models import Sum
        result = self.transactions.filter(
            transaction_type='submission',
            is_reversed=False,
            is_deleted=False
        ).aggregate(total=Sum('amount'))
        return result['total'] or 0

    @property
    def total_purchased(self):
        """Total purchases (ক্রয়) - only ACTIVE orders (non-reversed, non-cancelled, non-deleted)"""
        from django.db.models import Sum
        purchases = self.transactions.filter(
            transaction_type='purchase',
            is_reversed=False,
            is_deleted=False
        ).exclude(
            status='cancelled'  # Exclude cancelled orders
        )
        
        # Sum due_amount for each purchase (not full amount)
        total_due = 0
        for purchase in purchases:
            due_amount = purchase.due_amount if hasattr(purchase, 'due_amount') else purchase.amount
            total_due += due_amount
        
        return abs(total_due)
    
    @property
    def total_purchase_amount(self):
        """Total purchase amount (ক্রয়ের মোট পরিমাণ) - sum of all purchase transaction amounts"""
        from django.db.models import Sum
        purchases = self.transactions.filter(
            transaction_type='purchase',
            is_reversed=False,
            is_deleted=False
        ).exclude(
            status='cancelled'  # Exclude cancelled orders
        )
        
        # Sum the full amount for each purchase
        total_amount = purchases.aggregate(total=Sum('amount'))['total'] or 0
        return abs(total_amount)

    @property
    def total_withdrawn(self):
        """Total withdrawals (উত্তোলন) - only non-reversed withdrawals and non-deleted"""
        from django.db.models import Sum
        result = self.transactions.filter(
            transaction_type='withdrawal',
            is_reversed=False,
            is_deleted=False
        ).aggregate(total=Sum('amount'))
        return abs(result['total'] or 0)
    
    def recalculate_balance(self):
        """
        Recalculate customer balance based on ACTIVE transactions only.
        
        Balance Calculation Rules:
        - মোট জমা (Total Deposits) = Sum of all non-reversed submissions
        - মোট ক্রয় (Total Purchases) = Sum of all ACTIVE orders (non-reversed, non-cancelled)
        - মোট উত্তোলন (Total Withdrawals) = Sum of all non-reversed withdrawals
        - বর্তমান ব্যালেন্স = মোট জমা - মোট ক্রয় - মোট উত্তোলন
        
        Display Rules:
        - If balance < 0: Show as negative with "(বাকি)" - customer owes money
        - If balance > 0: Show as positive with "(কাস্টমার পাবে)" - customer has credit
        - If balance = 0: Show as 0
        """
        balance = Decimal('0.00')
        
        # Get all ACTIVE transactions (non-reversed, non-deleted)
        transactions = self.transactions.filter(
            is_reversed=False,
            is_deleted=False
        ).order_by('created_at')
        
        for txn in transactions:
            # Skip cancelled purchase orders - they should not affect balance
            if txn.transaction_type == 'purchase' and txn.status == 'cancelled':
                continue
                
            if txn.transaction_type == 'submission':
                balance += txn.amount
            elif txn.transaction_type == 'purchase':
                # Subtract due amount, not full amount (consider cash paid)
                due_amount = txn.due_amount if hasattr(txn, 'due_amount') else txn.amount
                balance -= due_amount
            elif txn.transaction_type == 'withdrawal':
                balance -= abs(txn.amount)
            elif txn.transaction_type == 'adjustment':
                balance += txn.amount
        
        self.current_balance = balance
        return balance


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
    
    # Cash payment tracking (for purchase transactions)
    cash_paid = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Cash Paid', default=0)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Due Amount', default=0)
    
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
        
        # Calculate balance_before and balance_after for this transaction
        # But DON'T update customer balance here - do it after save
        self.balance_before = self.customer.current_balance
        
        if self.transaction_type == 'submission':
            self.balance_after = self.balance_before + self.amount
        elif self.transaction_type == 'purchase':
            # For purchase: subtract due amount, not full amount
            due_amount = self.due_amount if hasattr(self, 'due_amount') else abs(self.amount)
            self.balance_after = self.balance_before - due_amount
        elif self.transaction_type == 'withdrawal':
            self.balance_after = self.balance_before - abs(self.amount)
        elif self.transaction_type == 'adjustment':
            self.balance_after = self.balance_before + self.amount
        elif self.transaction_type == 'reversal':
            # For reversal, reverse the original transaction's effect
            if self.reverses_transaction:
                if self.reverses_transaction.transaction_type == 'reversal':
                    if self.reverses_transaction.reverses_transaction:
                        original_txn = self.reverses_transaction.reverses_transaction
                        if original_txn.transaction_type == 'submission':
                            self.balance_after = self.balance_before + abs(original_txn.amount)
                        else:
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
        
        # CRITICAL FIX: Recalculate customer balance from ALL active transactions
        # This ensures balance is always correct regardless of order status changes
        new_balance = self.customer.recalculate_balance()
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
