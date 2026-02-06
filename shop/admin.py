from django.contrib import admin
from .models import ShopInfo, Product, Order


@admin.register(ShopInfo)
class ShopInfoAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'whatsapp']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'estimated_price', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'mobile_number', 'product_name', 'total_price', 'due_amount', 'status', 'order_date']
    list_filter = ['status', 'order_date', 'delivery_date']
    search_fields = ['customer_name', 'mobile_number', 'product_name']
    readonly_fields = ['due_amount', 'created_at', 'updated_at']

