from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('api/notifications/count/', views.notification_count_api, name='notification_count_api'),
    
    # Order Management
    path('order/create/', views.order_create, name='order_create'),
    path('import-legacy-orders/', views.import_legacy_orders, name='import_legacy_orders'),
    
    # Customer Management
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    path('customers/bulk-delete/', views.customer_bulk_delete, name='customer_bulk_delete'),
    
    # Transaction Management - Submission (Deposit)
    path('customers/<int:customer_pk>/submission/create/', 
         views.transaction_submission_create, name='transaction_submission_create'),
    
    # Transaction Management - Purchase
    path('customers/<int:customer_pk>/purchase/create/', 
         views.transaction_purchase_create, name='transaction_purchase_create'),
    
    # Transaction Management - Withdrawal
    path('customers/<int:customer_pk>/withdrawal/create/', 
         views.transaction_withdrawal_create, name='transaction_withdrawal_create'),
    
    # Transaction Voucher & List
    path('transactions/<int:pk>/voucher/', views.transaction_voucher, name='transaction_voucher'),
    path('customers/<int:customer_pk>/transactions/', views.transaction_list, name='transaction_list'),
    
    # Transaction Actions
    path('transactions/<int:pk>/reverse/', views.transaction_reverse, name='transaction_reverse'),
    path('transactions/<int:pk>/edit/', views.transaction_edit, name='transaction_edit'),
    path('transactions/<int:pk>/complete/', views.transaction_complete, name='transaction_complete'),
    
    # Customer Statements & History
    path('customers/<int:customer_pk>/statement/', views.customer_statement, name='customer_statement'),
    path('customers/<int:customer_pk>/history/', views.customer_history, name='customer_history'),
    
    # API Endpoints
    path('api/customer-search/', views.customer_search_api, name='customer_search_api'),
    
    # ==================== DEPRECATED URLS (Keep for backward compatibility) ====================
    path('submissions/create/<int:customer_pk>/', views.submission_create, name='submission_create'),
    path('submissions/<int:pk>/', views.submission_detail, name='submission_detail'),
    path('submissions/<int:submission_pk>/add-item/', views.submission_add_item, name='submission_add_item'),
    path('items/<int:item_pk>/remove/', views.submission_remove_item, name='submission_remove_item'),
]