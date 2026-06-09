from django.db import models
from django.utils import timezone
from decimal import Decimal
from transactions.models import Customer


class Invoice(models.Model):
    """Invoice model for managing customer invoices"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name='Invoice Number', editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='invoices', verbose_name='Customer')
    
    # Dates
    invoice_date = models.DateField(default=timezone.now, verbose_name='Invoice Date')
    due_date = models.DateField(verbose_name='Due Date')
    
    # Financial Information
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Subtotal')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Discount %')
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Discount Amount', editable=False)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Tax %')
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Tax Amount', editable=False)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total Amount', editable=False)
    
    # Payment Information
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Paid Amount')
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Due Amount', editable=False)
    
    # Status and Notes
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='Status')
    notes = models.TextField(verbose_name='Notes', blank=True)
    terms = models.TextField(verbose_name='Terms & Conditions', blank=True)
    
    # Audit Information
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices_created', verbose_name='Created By')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')
    
    class Meta:
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['customer', '-invoice_date']),
            models.Index(fields=['status']),
            models.Index(fields=['invoice_number']),
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        # Generate invoice number if not exists
        if not self.invoice_number:
            year = timezone.now().year
            last_invoice = Invoice.objects.filter(
                invoice_number__startswith=f'INV-{year}'
            ).order_by('-invoice_number').first()
            
            if last_invoice and last_invoice.invoice_number:
                try:
                    last_num = int(last_invoice.invoice_number.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            self.invoice_number = f"INV-{year}-{new_num:05d}"
        
        # Calculate amounts
        self.discount_amount = (self.subtotal * self.discount_percentage) / 100
        self.tax_amount = ((self.subtotal - self.discount_amount) * self.tax_percentage) / 100
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount
        self.due_amount = self.total_amount - self.paid_amount
        
        # Update status based on payment
        if self.paid_amount >= self.total_amount:
            self.status = 'paid'
        elif self.paid_amount > 0:
            self.status = 'partial'
        
        super().save(*args, **kwargs)


class InvoiceItem(models.Model):
    """Invoice line items"""
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items', verbose_name='Invoice')
    product_name = models.CharField(max_length=200, verbose_name='Product Name')
    product_description = models.TextField(verbose_name='Description', blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Quantity')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Unit Price')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Discount %')
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Discount Amount', editable=False)
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Gross Amount', editable=False)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Net Amount', editable=False)
    
    class Meta:
        verbose_name = 'Invoice Item'
        verbose_name_plural = 'Invoice Items'
    
    def save(self, *args, **kwargs):
        self.gross_amount = self.quantity * self.unit_price
        self.discount_amount = (self.gross_amount * self.discount_percentage) / 100
        self.net_amount = self.gross_amount - self.discount_amount
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product_name} - {self.invoice.invoice_number}"


class InvoicePayment(models.Model):
    """Track payments made against invoices"""
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card'),
        ('other', 'Other'),
    ]
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', verbose_name='Invoice')
    payment_date = models.DateField(default=timezone.now, verbose_name='Payment Date')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Amount')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash', verbose_name='Payment Method')
    reference_number = models.CharField(max_length=100, verbose_name='Reference Number', blank=True)
    notes = models.TextField(verbose_name='Notes', blank=True)
    
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Created By')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    
    class Meta:
        verbose_name = 'Invoice Payment'
        verbose_name_plural = 'Invoice Payments'
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment for {self.invoice.invoice_number} - ৳{self.amount}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update invoice paid amount
        self.invoice.paid_amount = self.invoice.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        self.invoice.save()