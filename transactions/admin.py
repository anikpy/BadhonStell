from django.contrib import admin
from .models import Customer, Transaction, TransactionItem, TransactionHistory, CustomerSubmission, CustomerItem


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'mobile_number', 'current_balance', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'mobile_number']
    readonly_fields = ['current_balance', 'created_at', 'updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_number', 'customer', 'transaction_type', 'amount', 'status', 'created_at']
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['transaction_number', 'customer__name', 'customer__mobile_number']
    readonly_fields = ['transaction_number', 'balance_before', 'balance_after', 'created_at', 'updated_at']
    autocomplete_fields = ['customer', 'inventory_product', 'reverses_transaction', 'original_transaction']


@admin.register(TransactionItem)
class TransactionItemAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'product_name', 'quantity', 'unit_price', 'net_amount']
    list_filter = ['transaction__transaction_type']
    search_fields = ['product_name', 'transaction__transaction_number']
    autocomplete_fields = ['transaction', 'inventory_product']


@admin.register(TransactionHistory)
class TransactionHistoryAdmin(admin.ModelAdmin):
    list_display = ['transaction', 'action', 'old_balance', 'new_balance', 'performed_by', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['transaction__transaction_number', 'notes']
    readonly_fields = ['created_at']
    autocomplete_fields = ['transaction', 'performed_by']


@admin.register(CustomerSubmission)
class CustomerSubmissionAdmin(admin.ModelAdmin):
    list_display = ['customer', 'submitted_amount', 'submission_date']
    list_filter = ['submission_date']
    search_fields = ['customer__name', 'customer__mobile_number']
    readonly_fields = ['submission_date']


@admin.register(CustomerItem)
class CustomerItemAdmin(admin.ModelAdmin):
    list_display = ['submission', 'product_name', 'quantity', 'unit_price', 'total_price']
    list_filter = ['added_date']
    search_fields = ['product_name', 'submission__customer__name']
    autocomplete_fields = ['submission']