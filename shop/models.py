from django.db import models
from django.utils import timezone


class ShopInfo(models.Model):
    """দোকানের তথ্য"""
    name = models.CharField(max_length=200, verbose_name='দোকানের নাম')
    logo = models.ImageField(upload_to='shop/', blank=True, null=True, verbose_name='লোগো')
    description = models.TextField(verbose_name='বিবরণ')
    phone = models.CharField(max_length=20, verbose_name='ফোন নাম্বার')
    whatsapp = models.CharField(max_length=20, verbose_name='হোয়াটসঅ্যাপ নাম্বার')
    address = models.TextField(verbose_name='ঠিকানা', blank=True)
    
    class Meta:
        verbose_name = 'দোকানের তথ্য'
        verbose_name_plural = 'দোকানের তথ্য'
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """পণ্যের মডেল"""
    PRODUCT_CATEGORIES = [
        ('door', 'দরজা'),
        ('window', 'জানালা'),
        ('grill', 'গ্রিল'),
        ('gate', 'গেট'),
        ('railing', 'রেলিং'),
        ('shed', 'শেড'),
        ('other', 'অন্যান্য'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='পণ্যের নাম')
    category = models.CharField(max_length=50, choices=PRODUCT_CATEGORIES, verbose_name='ক্যাটাগরি')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='ছবি')
    description = models.TextField(verbose_name='বিবরণ')
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='আনুমানিক দাম')
    is_active = models.BooleanField(default=True, verbose_name='সক্রিয়')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='তৈরির তারিখ')
    
    class Meta:
        verbose_name = 'পণ্য'
        verbose_name_plural = 'পণ্যসমূহ'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class InventoryProduct(models.Model):
    """ইনভেন্টরি পণ্য - স্টক ব্যবস্থাপনার জন্য"""
    UNIT_CHOICES = [
        ('piece', 'পিস'),
        ('feet', 'ফুট'),
        ('meter', 'মিটার'),
        ('ton', 'টন'),
        ('kg', 'কেজি'),
    ]

    name = models.CharField(max_length=200, verbose_name='পণ্যের নাম')
    description = models.TextField(verbose_name='বিবরণ', blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, verbose_name='একক')
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='প্রতি একক মূল্য')
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='স্টক পরিমাণ', default=0)
    is_active = models.BooleanField(default=True, verbose_name='সক্রিয়')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='তৈরির তারিখ')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='আপডেটের তারিখ')
    # Optional image for inventory product
    image = models.ImageField(upload_to='inventory/', blank=True, null=True, verbose_name='ছবি')

    class Meta:
        verbose_name = 'ইনভেন্টরি পণ্য'
        verbose_name_plural = 'ইনভেন্টরি পণ্যসমূহ'
        ordering = ['name']
        # Prevent duplicate products with same name and unit
        unique_together = [['name', 'unit']]

    def __str__(self):
        return f"{self.name} ({self.stock_quantity} {self.get_unit_display()})"
    
    def add_stock(self, quantity):
        """Add stock to existing product"""
        if quantity <= 0:
            raise ValueError("স্টক পরিমাণ ০-এর বেশি হতে হবে")
        self.stock_quantity += quantity
        self.save()
    
    def remove_stock(self, quantity):
        """Remove stock from existing product"""
        if quantity <= 0:
            raise ValueError("স্টক পরিমাণ ০-এর বেশি হতে হবে")
        if self.stock_quantity < quantity:
            raise ValueError(f"অপর্যাপ্ত স্টক! বর্তমান স্টক: {self.stock_quantity}")
        self.stock_quantity -= quantity
        self.save()


class Order(models.Model):
    """অর্ডার মডেল - একাধিক পণ্যের জন্য"""
    STATUS_CHOICES = [
        ('pending', 'চলমান'),
        ('ready', 'প্রস্তুত'),
        ('completed', 'সম্পন্ন'),
    ]

    DELIVERY_STATUS_CHOICES = [
        ('not_delivered', 'ডেলিভারি হয়নি'),
        ('delivered', 'ডেলিভারি সম্পন্ন'),
    ]

    customer_name = models.CharField(max_length=200, verbose_name='ক্রেতার নাম')
    mobile_number = models.CharField(max_length=20, verbose_name='মোবাইল নাম্বার')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='মোট মূল্য', default=0)
    cash_paid = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='নগদ পরিশোধ', default=0)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='বাকি টাকা', editable=False)
    initial_payment_migrated = models.BooleanField(default=False, verbose_name='প্রাথমিক পেমেন্ট OrderPayment-এ স্থানান্তরিত')
    order_date = models.DateField(default=timezone.now, verbose_name='অর্ডার নেওয়ার তারিখ')
    delivery_date = models.DateField(verbose_name='ডেলিভারির তারিখ')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='প্রোডাক্ট অবস্থা')
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='not_delivered', verbose_name='ডেলিভারি অবস্থা')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='তৈরির সময়')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='আপডেটের সময়')

    class Meta:
        verbose_name = 'অর্ডার'
        verbose_name_plural = 'অর্ডারসমূহ'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Calculate total_price from items if not set
        if not self.total_price:
            total = sum(item.total_price for item in self.items.all())
            self.total_price = total
        
        # Calculate due_amount
        self.due_amount = self.total_price - self.cash_paid
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_name} - Order #{self.pk}"


class OrderItem(models.Model):
    """অর্ডার আইটেম - একটি অর্ডারে একাধিক পণ্য"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='অর্ডার')
    product_name = models.CharField(max_length=200, verbose_name='পণ্যের নাম')
    product_description = models.TextField(verbose_name='পণ্যের বিবরণ', blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='পরিমাণ', default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='একক মূল্য')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='মোট মূল্য', editable=False)
    
    class Meta:
        verbose_name = 'অর্ডার আইটেম'
        verbose_name_plural = 'অর্ডার আইটেমসমূহ'
    
    def save(self, *args, **kwargs):
        # Calculate total_price
        self.total_price = self.quantity * self.unit_price
        
        # Check stock availability for inventory products
        try:
            inventory_product = InventoryProduct.objects.filter(name__iexact=self.product_name).first()
            if inventory_product:
                if inventory_product.stock_quantity < self.quantity:
                    raise ValueError(f"অপর্যাপ্ত স্টক! {self.product_name}-এর বর্তমান স্টক: {inventory_product.stock_quantity} {inventory_product.get_unit_display()}, অর্ডার করা হয়েছে: {self.quantity}")
        except:
            pass  # If no matching inventory product found, skip stock check
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product_name} × {self.quantity} - Order #{self.order.pk}"


class Invoice(models.Model):
    """ইনভয়েস/ভাউচার - সিম্পল বিক্রয় রেকর্ড"""
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name='ইনভয়েস নাম্বার', editable=False)

    # কাস্টমার তথ্য
    customer_name = models.CharField(max_length=200, verbose_name='ক্রেতার নাম')
    mobile_number = models.CharField(max_length=20, verbose_name='মোবাইল নাম্বার')

    # পণ্যের তথ্য (backward compat: nullable for multi-item invoices)
    product = models.ForeignKey(InventoryProduct, on_delete=models.PROTECT, verbose_name='পণ্য',
                                null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='পরিমাণ', default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='একক মূল্য', default=0)

    # মূল্য হিসাব
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='সাবটোটাল', editable=False, default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='ছাড় (%)', default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='ছাড়ের টাকা', editable=False, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='মোট টাকা', editable=False, default=0)

    # পেমেন্ট তথ্য
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='পরিশোধিত টাকা', default=0)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='বাকি টাকা', editable=False, default=0)

    # অন্যান্য
    notes = models.TextField(verbose_name='নোট', blank=True)
    sale_date = models.DateField(default=timezone.now, verbose_name='বিক্রয়ের তারিখ')

    # ভাউচার এডিট ট্র্যাকিং
    original_invoice = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='edited_versions', verbose_name='মূল ইনভয়েস')
    is_latest = models.BooleanField(default=True, verbose_name='সর্বশেষ ভার্সন')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='তৈরির সময়')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='আপডেটের সময়')

    class Meta:
        verbose_name = 'ইনভয়েস'
        verbose_name_plural = 'ইনভয়েসসমূহ'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # ইনভয়েস নাম্বার জেনারেট
        if not self.invoice_number:
            last_invoice = Invoice.objects.all().order_by('-id').first()
            if last_invoice and last_invoice.invoice_number:
                try:
                    last_num = int(last_invoice.invoice_number.split('-')[-1])
                    self.invoice_number = f"INV-{last_num + 1:05d}"
                except:
                    self.invoice_number = "INV-00001"
            else:
                self.invoice_number = "INV-00001"

        if self.product_id:
            # Single-product mode (backward compatibility with old invoices)
            self.subtotal = self.quantity * self.unit_price
            self.discount_amount = (self.subtotal * self.discount_percentage) / 100
            self.total_amount = self.subtotal - self.discount_amount
            self.due_amount = self.total_amount - self.paid_amount

            # স্টক কমানো (শুধু নতুন ইনভয়েসের জন্য)
            if self.pk is None:
                if self.product.stock_quantity >= self.quantity:
                    self.product.stock_quantity -= self.quantity
                    self.product.save()
                else:
                    raise ValueError(f"স্টক অপর্যাপ্ত! বর্তমান স্টক: {self.product.stock_quantity}")
        else:
            # Multi-item mode: subtotal pre-calculated in view, just apply discount
            self.discount_amount = (self.subtotal * self.discount_percentage) / 100
            self.total_amount = self.subtotal - self.discount_amount
            self.due_amount = self.total_amount - self.paid_amount

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} - {self.customer_name}"

    @property
    def total_item_savings(self):
        """সকল আইটেমের ছাড়ের মোট পরিমাণ (multi-item মোডের জন্য)"""
        return sum(item.discount_amount for item in self.items.all())

    @property
    def total_gross_amount(self):
        """সকল আইটেমের গ্রস মোট (ছাড়ের আগে)"""
        return sum(item.gross_amount for item in self.items.all())

    def get_total_paid_amount(self):
        """আংশিক পেমেন্ট থেকে মোট পরিশোধিত পরিমাণ পান"""
        return sum(payment.amount for payment in self.payments.all())


class InvoiceItem(models.Model):
    """ইনভয়েস আইটেম - একটি ইনভয়েসে একাধিক পণ্যের জন্য (প্রতিটি পণ্যে আলাদা ছাড় সহ)"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items', verbose_name='ইনভয়েস')
    product = models.ForeignKey(InventoryProduct, on_delete=models.PROTECT, verbose_name='পণ্য')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='পরিমাণ')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='একক মূল্য')
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name='ছাড় (%)'
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, editable=False, default=0, verbose_name='ছাড়ের টাকা'
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='সাবটোটাল', editable=False, default=0)

    class Meta:
        verbose_name = 'ইনভয়েস আইটেম'
        verbose_name_plural = 'ইনভয়েস আইটেমসমূহ'

    def save(self, *args, **kwargs):
        gross = self.quantity * self.unit_price
        self.discount_amount = (gross * self.discount_percentage) / 100
        self.subtotal = gross - self.discount_amount
        super().save(*args, **kwargs)

    @property
    def gross_amount(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.invoice.invoice_number} – {self.product.name} × {self.quantity}"


class Payment(models.Model):
    """পেমেন্ট - আংশিক পেমেন্ট ট্র্যাকিং"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments', verbose_name='ইনভয়েস')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='পরিশোধিত পরিমাণ')
    payment_date = models.DateField(default=timezone.now, verbose_name='পেমেন্ট তারিখ')
    notes = models.TextField(verbose_name='নোট', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='তৈরির সময়')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='আপডেটের সময়')

    class Meta:
        verbose_name = 'পেমেন্ট'
        verbose_name_plural = 'পেমেন্টসমূহ'
        ordering = ['-payment_date']

    def __str__(self):
        return f"পেমেন্ট {self.amount} - {self.invoice.invoice_number}"


class OrderPayment(models.Model):
    """অর্ডার পেমেন্ট - কাস্টম অর্ডারের আংশিক পেমেন্ট ট্র্যাকিং"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', verbose_name='অর্ডার')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='পরিশোধিত পরিমাণ')
    payment_date = models.DateField(default=timezone.now, verbose_name='পেমেন্ট তারিখ')
    notes = models.TextField(verbose_name='নোট', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='তৈরির সময়')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='আপডেটের সময়')

    class Meta:
        verbose_name = 'অর্ডার পেমেন্ট'
        verbose_name_plural = 'অর্ডার পেমেন্টসমূহ'
        ordering = ['-payment_date']

    def __str__(self):
        return f"অর্ডার পেমেন্ট {self.amount} - Order#{self.order.pk}"

    def save(self, *args, **kwargs):
        # Prevent overpayment: sum existing payments (excluding this one if updating)
        existing_total = sum(p.amount for p in self.order.payments.exclude(pk=self.pk))
        new_total = existing_total + (self.amount or 0)
        if new_total > float(self.order.total_price):
            raise ValueError(f"Overpayment detected: order total is {self.order.total_price}, existing paid {existing_total}, attempted add {(self.amount or 0)}")
        super().save(*args, **kwargs)


# Signals to update Order totals when OrderPayment changes
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver([post_save, post_delete], sender=OrderPayment)
def update_order_payment_totals(sender, instance, **kwargs):
    """
    CRITICAL FIX: Properly calculate cash_paid and due_amount

    Design:
    - cash_paid field is used for initial payment when order is created (for convenience)
    - But once we add OrderPayment records, we should track EVERYTHING via OrderPayment
    - This signal migrates initial payment to OrderPayment on first payment addition
    """
    order = instance.order
    from decimal import Decimal

    # Step 1: If initial payment exists and not yet migrated, create OrderPayment for it.
    # CRITICAL: Always migrate the full order.cash_paid to an OrderPayment once. Otherwise
    # when the user adds a payment that equals or exceeds the initial amount, we skip
    # migration (existing_payment_total >= cash_paid) and then Step 2 overwrites
    # cash_paid with sum(OrderPayments), losing the initial payment.
    if order.cash_paid > 0 and not order.initial_payment_migrated:
        try:
            initial_amount = Decimal(str(order.cash_paid))
            OrderPayment.objects.create(
                order=order,
                amount=initial_amount,
                payment_date=order.order_date,
                notes='প্রাথমিক পেমেন্ট (মাইগ্রেটেড)'
            )
            order.initial_payment_migrated = True
        except Exception:
            pass  # Silently skip if migration fails

    # Step 2: Recalculate total paid from ALL OrderPayment records.
    # CRITICAL: On post_save, include the triggering instance explicitly — the reverse
    # relation order.payments.all() can miss the just-saved row, so the first payment
    # would not be counted until a second payment is added. On post_delete, instance is
    # already removed from DB so sum(order.payments.all()) is correct.
    if 'created' in kwargs and getattr(instance, 'pk', None):
        total_paid = sum(Decimal(str(p.amount)) for p in order.payments.exclude(pk=instance.pk)) + Decimal(str(instance.amount))
    else:
        total_paid = sum(Decimal(str(p.amount)) for p in order.payments.all())
    order.cash_paid = total_paid
    order.due_amount = order.total_price - total_paid
    order.initial_payment_migrated = True

    # Save without triggering signal again
    Order.objects.filter(pk=order.pk).update(
        cash_paid=order.cash_paid,
        due_amount=order.due_amount,
        initial_payment_migrated=True
    )