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

    # ইনভেন্টরি পণ্য ম্যানেজমেন্ট URLs
    path('admin-panel/inventory/', views.inventory_product_list, name='inventory_product_list'),
    path('admin-panel/inventory/create/', views.inventory_product_create, name='inventory_product_create'),
    path('admin-panel/inventory/<int:pk>/edit/', views.inventory_product_edit, name='inventory_product_edit'),
    path('admin-panel/inventory/<int:pk>/delete/', views.inventory_product_delete, name='inventory_product_delete'),
    path('admin-panel/inventory/<int:pk>/stock/', views.stock_management, name='stock_management'),


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
    path('admin-panel/customers/', views.customer_list, name='customer_list'),

]
