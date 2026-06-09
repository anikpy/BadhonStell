from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
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
    path('customers/trash/', views.customer_trash_list, name='customer_trash_list'),
    path('customers/<int:pk>/restore/', views.customer_restore, name='customer_restore'),
    
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
    path('<int:pk>/voucher/', views.transaction_voucher, name='transaction_voucher'),
    path('list/', views.transaction_list_all, name='transaction_list_all'),
    path('customers/<int:customer_pk>/transactions/', views.transaction_list, name='transaction_list'),
    
    # Transaction Actions
    path('<int:pk>/reverse/', views.transaction_reverse, name='transaction_reverse'),
    path('<int:pk>/edit/', views.transaction_edit, name='transaction_edit'),
    path('<int:pk>/complete/', views.transaction_complete, name='transaction_complete'),
    path('<int:pk>/update-status/', views.transaction_update_status, name='transaction_status_update'),
    
    # Customer Statements & History
    path('customers/<int:customer_pk>/statement/', views.customer_statement, name='customer_statement'),
    path('customers/<int:customer_pk>/history/', views.customer_history, name='customer_history'),
    path('customers/<int:customer_pk>/notes/add/', views.customer_note_create, name='customer_note_create'),
    
    # API Endpoints
    path('api/customer-search/', views.customer_search_api, name='customer_search_api'),
    path('api/customers/<int:customer_pk>/notes/', views.customer_notes_api, name='customer_notes_api'),
    
    # ==================== DEPRECATED URLS (Keep for backward compatibility) ====================
    path('submissions/create/<int:customer_pk>/', views.submission_create, name='submission_create'),
    path('submissions/<int:pk>/', views.submission_detail, name='submission_detail'),
    path('submissions/<int:submission_pk>/add-item/', views.submission_add_item, name='submission_add_item'),
    path('items/<int:item_pk>/remove/', views.submission_remove_item, name='submission_remove_item'),
]