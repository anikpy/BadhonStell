from django.contrib import admin
from .models import ShopInfo, Product, Order, OrderItem, InventoryProduct, Invoice, InvoiceItem, Payment, OrderPayment


@admin.register(ShopInfo)
class ShopInfoAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'whatsapp']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'estimated_price', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'unit_price', 'total_price']
    search_fields = ['product_name', 'order__customer_name']
    readonly_fields = ['total_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'mobile_number', 'get_products', 'total_price', 'due_amount', 'status', 'order_date']
    list_filter = ['status', 'order_date', 'delivery_date']
    search_fields = ['customer_name', 'mobile_number']
    readonly_fields = ['due_amount', 'created_at', 'updated_at']
    
    def get_products(self, obj):
        """Display products as comma-separated list"""
        products = [item.product_name for item in obj.items.all()]
        return ', '.join(products) if products else 'No products'
    get_products.short_description = 'Products'


@admin.register(InventoryProduct)
class InventoryProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit', 'price_per_unit', 'stock_quantity', 'is_active', 'created_at']
    list_filter = ['unit', 'is_active']
    search_fields = ['name', 'description']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer_name', 'mobile_number', 'total_amount', 'paid_amount', 'due_amount', 'sale_date']
    list_filter = ['sale_date', 'is_latest']
    search_fields = ['invoice_number', 'customer_name', 'mobile_number']
    readonly_fields = ['invoice_number', 'subtotal', 'discount_amount', 'total_amount', 'due_amount', 'created_at']


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'product', 'quantity', 'unit_price', 'discount_percentage', 'subtotal']
    search_fields = ['product__name', 'invoice__customer_name']
    readonly_fields = ['discount_amount', 'subtotal']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'payment_date', 'notes']
    list_filter = ['payment_date']
    search_fields = ['invoice__invoice_number', 'invoice__customer_name']


@admin.register(OrderPayment)
class OrderPaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'amount', 'payment_date', 'notes']
    list_filter = ['payment_date']
    search_fields = ['order__customer_name']

