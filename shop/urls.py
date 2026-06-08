from django.urls import path
from . import views

urlpatterns = [
    # কাস্টমার সাইট URLs
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),

    # অ্যাডমিন প্যানেল URLs
    path('admin-panel/login/', views.admin_login, name='admin_login'),
    path('admin-panel/logout/', views.admin_logout, name='admin_logout'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),

    # অর্ডার ম্যানেজমেন্ট URLs (কাস্টম পণ্য)
    path('admin-panel/orders/', views.order_list, name='order_list'),
    path('admin-panel/orders/completed/', views.completed_order_list, name='completed_order_list'),
    path('admin-panel/orders/create/', views.order_create, name='order_create'),
    path('admin-panel/orders/<int:pk>/edit/', views.order_edit, name='order_edit'),
    path('admin-panel/orders/<int:pk>/delete/', views.order_delete, name='order_delete'),
    path('admin-panel/orders/<int:pk>/complete/', views.order_complete, name='order_complete'),
    path('admin-panel/orders/<int:order_pk>/payment/', views.order_payment_create, name='order_payment_create'),
    path('admin-panel/orders/payments/<int:pk>/edit/', views.order_payment_edit, name='order_payment_edit'),
    path('admin-panel/orders/payments/<int:pk>/delete/', views.order_payment_delete, name='order_payment_delete'),
    path('admin-panel/orders/<int:pk>/voucher/', views.order_voucher, name='order_voucher'),
    path('admin-panel/customers/<int:customer_pk>/combined-voucher/', views.customer_combined_voucher, name='customer_combined_voucher'),

    # ক্রেতা ব্যবস্থাপনা URLs (Customer Management - Custom Orders)
    path('admin-panel/customers/new/', views.customer_list_new, name='customer_list_new'),
    path('admin-panel/customers/new/create/', views.customer_create, name='customer_create'),
    path('admin-panel/customers/new/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('admin-panel/customers/new/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('admin-panel/customers/new/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    path('admin-panel/customers/new/<int:customer_pk>/deposit/', views.customer_deposit_create, name='customer_deposit_create'),
    path('admin-panel/customers/new/<int:customer_pk>/deposits/', views.customer_deposit_list, name='customer_deposit_list'),
    path('admin-panel/customers/new/deposits/<int:pk>/edit/', views.customer_deposit_edit, name='customer_deposit_edit'),
    path('admin-panel/customers/new/deposits/<int:pk>/delete/', views.customer_deposit_delete, name='customer_deposit_delete'),
    path('admin-panel/customers/new/<int:pk>/statement/', views.customer_statement, name='customer_statement'),
    path('admin-panel/customers/new/<int:customer_pk>/order/create/', views.order_create_for_customer, name='order_create_for_customer'),

    # ইনভেন্টরি পণ্য ম্যানেজমেন্ট URLs
    path('admin-panel/inventory/', views.inventory_product_list, name='inventory_product_list'),
    path('admin-panel/inventory/create/', views.inventory_product_create, name='inventory_product_create'),
    path('admin-panel/inventory/<int:pk>/edit/', views.inventory_product_edit, name='inventory_product_edit'),
    path('admin-panel/inventory/<int:pk>/delete/', views.inventory_product_delete, name='inventory_product_delete'),
    path('admin-panel/inventory/<int:pk>/stock/', views.stock_management, name='stock_management'),
    path('admin-panel/inventory/print-pdf/', views.print_inventory_pdf, name='print_inventory_pdf'),
    path('admin-panel/inventory/print-selected-pdf/', views.print_selected_inventory_pdf, name='print_selected_inventory_pdf'),
    path('admin-panel/inventory/bulk-price-update/', views.bulk_price_update, name='bulk_price_update'),
    path('admin-panel/inventory/price-history/', views.price_history_list, name='price_history_list'),
    path('admin-panel/inventory/price-history/<int:pk>/revert/', views.price_history_revert, name='price_history_revert'),
    path('admin-panel/inventory/price-history/bulk-revert/', views.price_history_bulk_revert, name='price_history_bulk_revert'),
    path('admin-panel/inventory/print-history-pdf/', views.print_stock_history_pdf, name='print_stock_history_pdf'),


    # ইনভয়েস/ভাউচার URLs
    path('admin-panel/invoices/', views.invoice_list, name='invoice_list'),
    path('admin-panel/invoices/create/', views.invoice_create, name='invoice_create'),
    path('admin-panel/invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('admin-panel/invoices/<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),
    path('admin-panel/invoices/<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    path('admin-panel/invoices/<int:invoice_pk>/payment/', views.payment_create, name='payment_create'),
    path('admin-panel/payments/<int:pk>/edit/', views.payment_edit, name='payment_edit'),
    path('admin-panel/payments/<int:pk>/delete/', views.payment_delete, name='payment_delete'),
    path('admin-panel/customer/<str:mobile_number>/', views.customer_profile, name='customer_profile'),
    path('admin-panel/order-customer/<str:mobile_number>/', views.order_customer_profile, name='order_customer_profile'),

    # ইউজার ম্যানেজমেন্ট URLs (শুধু সুপার অ্যাডমিনের জন্য)
    path('admin-panel/users/', views.user_management, name='user_management'),
    path('admin-panel/users/create/', views.user_create, name='user_create'),
    path('admin-panel/users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('admin-panel/users/<int:user_id>/reset-password/', views.user_reset_password, name='user_reset_password'),

    # অ্যাডমিন স্ট্যাটিস্টিক্স URLs (শুধু সুপার অ্যাডমিনের জন্য)
    path('admin-panel/statistics/', views.admin_statistics, name='admin_statistics'),

    # বাকি খাতা এবং কাস্টমার লিস্ট URLs
    path('admin-panel/due-accounts/', views.due_accounts_list, name='due_accounts_list'),
    path('admin-panel/due-accounts/print/', views.due_accounts_print, name='due_accounts_print'),
    path('admin-panel/customers/', views.customer_list, name='customer_list'),

    # API endpoint for customer search (autocomplete)
    path('api/customers/search/', views.customer_search_api, name='customer_search_api'),
    
    # অর্ডার কাস্টমার URLs (Order Management System)
    path('admin-panel/order-customers/', views.test_customer_list, name='order_customer_list'),
    path('admin-panel/order-customers/create/', views.test_customer_create, name='order_customer_create'),
    path('admin-panel/orders/new/', views.test_order_create, name='order_create_new'),
    path('admin-panel/order-customers/<int:pk>/', views.test_customer_detail, name='order_customer_detail'),
    path('admin-panel/order-customers/<int:pk>/edit/', views.test_customer_edit, name='order_customer_edit'),
    path('admin-panel/order-customers/<int:pk>/delete/', views.test_customer_delete, name='order_customer_delete'),
    path('admin-panel/order-customers/bulk-delete/', views.test_customer_bulk_delete, name='order_customer_bulk_delete'),
    
    # লেনদেন URLs (Transaction URLs)
    path('admin-panel/order-customers/<int:customer_pk>/submission/', views.test_transaction_submission_create, name='transaction_submission_create'),
    path('admin-panel/order-customers/<int:customer_pk>/purchase/', views.test_transaction_purchase_create, name='transaction_purchase_create'),
    path('admin-panel/order-customers/<int:customer_pk>/withdrawal/', views.test_transaction_withdrawal_create, name='transaction_withdrawal_create'),
    path('admin-panel/order-customers/<int:customer_pk>/transactions/', views.test_transaction_list, name='transaction_list'),
    path('admin-panel/order-customers/<int:customer_pk>/statement/', views.test_customer_statement, name='order_customer_statement'),
    path('admin-panel/order-customers/<int:customer_pk>/history/', views.test_customer_history, name='order_customer_history'),
    path('admin-panel/transactions/<int:pk>/voucher/', views.test_transaction_voucher, name='transaction_voucher'),
    path('admin-panel/transactions/<int:pk>/reverse/', views.test_transaction_reverse, name='transaction_reverse'),
    path('admin-panel/transactions/<int:pk>/edit/', views.test_transaction_edit, name='transaction_edit'),
    
    # পুরাতন URLs - Backward compatibility
    path('admin-panel/test-customers/<int:customer_pk>/submission-old/', views.test_submission_create, name='test_submission_create'),
    path('admin-panel/test-submissions/<int:pk>/', views.test_submission_detail, name='test_submission_detail'),
    path('admin-panel/test-submissions/<int:submission_pk>/item/add/', views.test_submission_add_item, name='test_submission_add_item'),
    path('admin-panel/test-submissions/item/<int:item_pk>/remove/', views.test_submission_remove_item, name='test_submission_remove_item'),

]
