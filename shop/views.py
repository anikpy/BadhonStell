from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from django.http import HttpResponse, JsonResponse
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from .models import (
    ShopInfo,
    Product,
    Order,
    InventoryProduct,
    Invoice,
    InvoiceItem,
    OrderItem,
    Payment,
    OrderPayment,
    StockHistory,
    Customer,
    PriceHistory,
    CustomerDeposit,
    TestCustomer,
    TestCustomerSubmission,
    TestCustomerItem,
    TestCustomerTransaction,
    TestCustomerTransactionItem,
    TestTransactionHistory,
)
from .forms import (
    OrderForm, InventoryProductForm, InvoiceForm, PaymentForm, OrderPaymentForm, 
    StockManagementForm, CustomerForm, CustomerDepositForm, TestCustomerForm, 
    TestCustomerSubmissionForm, TestTransactionSubmissionForm, 
    TestTransactionPurchaseForm, TestTransactionWithdrawalForm
)
from decimal import Decimal
import json


# কাস্টমার সাইট ভিউ
def home(request):
    """হোম পেজ - এখন ইনভেন্টরি থেকে ডায়নামিক পণ্য দেখায়"""
    shop_info = ShopInfo.objects.first()
    # Show inventory items uploaded via admin panel
    products = InventoryProduct.objects.filter(is_active=True)

    context = {
        'shop_info': shop_info,
        'products': products,
    }
    return render(request, 'shop/home.html', context)


def product_list(request):
    """পণ্য তালিকা"""
    shop_info = ShopInfo.objects.first()
    category = request.GET.get('category', '')

    if category:
        products = Product.objects.filter(is_active=True, category=category)
    else:
        products = Product.objects.filter(is_active=True)

    context = {
        'shop_info': shop_info,
        'products': products,
        'selected_category': category,
    }
    return render(request, 'shop/products.html', context)


from django.views.decorators.csrf import csrf_exempt

# কাস্টম অ্যাডমিন প্যানেল ভিউ
@csrf_exempt  # Temporarily disable CSRF for login behind proxy
def admin_login(request):
    """অ্যাডমিন লগইন"""
    if request.user.is_authenticated:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'ভুল ইউজারনেম অথবা পাসওয়ার্ড!')

    return render(request, 'admin_panel/login.html')


@login_required
def admin_logout(request):
    """অ্যাডমিন লগআউট"""
    logout(request)
    return redirect('admin_login')


@login_required
def admin_dashboard(request):
    """অ্যাডমিন ড্যাশবোর্ড"""
    # Get order statistics from transactions app instead of shop app
    from transactions.models import Transaction
    
    total_orders = Transaction.objects.count()
    pending_orders = Transaction.objects.filter(status='pending').count()
    completed_orders = Transaction.objects.filter(status='completed', delivery_status='delivered').count()
    completed_not_delivered = Transaction.objects.filter(status='completed', delivery_status='not_delivered').count()

    # শুধু চলমান অর্ডার (সম্পন্ন অর্ডার দেখাবেন না)
    recent_orders = Order.objects.exclude(status='completed').order_by('status', '-created_at')[:10]

    # Get recent customer notes (only non-dismissed from dashboard)
    from transactions.models import CustomerNote
    recent_notes = CustomerNote.objects.filter(is_dismissed_from_dashboard=False).select_related('customer', 'created_by').order_by('-created_at')[:10]

    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'completed_not_delivered': completed_not_delivered,
        'recent_orders': recent_orders,
        'recent_notes': recent_notes,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
def order_list(request):
    """অর্ডার তালিকা - ক্রেতা অনুযায়ী গ্রুপ করা"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    delivery_status_filter = request.GET.get('delivery_status', '')
    date_filter = request.GET.get('date_filter', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    payment_status = request.GET.get('payment_status', '')
    page_number = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', '15')
    
    # Validate per_page
    try:
        per_page = int(per_page)
        if per_page not in [15, 50, 100, 200]:
            per_page = 15
    except ValueError:
        per_page = 15

    # Show all orders
    orders = Order.objects.all().select_related('customer').prefetch_related('items').order_by('-created_at')
    
    # Apply date filters
    today = timezone.now().date()
    
    if date_filter == 'today':
        orders = orders.filter(order_date=today)
    elif date_filter == 'week':
        week_ago = today - timedelta(days=7)
        orders = orders.filter(order_date__gte=week_ago)
    elif date_filter == 'month':
        month_ago = today - timedelta(days=30)
        orders = orders.filter(order_date__gte=month_ago)
    elif date_filter == 'year':
        year_ago = today - timedelta(days=365)
        orders = orders.filter(order_date__gte=year_ago)
    elif date_filter == 'custom' and from_date and to_date:
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            orders = orders.filter(order_date__range=[from_date_obj, to_date_obj])
        except ValueError:
            pass
    
    # Apply payment status filter
    if payment_status == 'paid':
        orders = orders.filter(due_amount=0)
    elif payment_status == 'due':
        orders = orders.filter(due_amount__gt=0)
    elif payment_status == 'partial':
        orders = orders.filter(cash_paid__gt=0, due_amount__gt=0)

    if search_query:
        orders = orders.filter(
            Q(customer_name__icontains=search_query) |
            Q(mobile_number__icontains=search_query) |
            Q(items__product_name__icontains=search_query)
        ).distinct()

    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if delivery_status_filter:
        orders = orders.filter(delivery_status=delivery_status_filter)
    
    # Group orders by customer
    from collections import defaultdict
    customer_orders = defaultdict(list)
    for order in orders:
        # Use customer if available, otherwise use customer_name + mobile
        if order.customer:
            key = f"customer_{order.customer.pk}"
            customer_orders[key].append({
                'order': order,
                'customer': order.customer,
                'customer_name': order.customer.name,
                'mobile_number': order.customer.mobile_number,
            })
        else:
            key = f"manual_{order.customer_name}_{order.mobile_number}"
            customer_orders[key].append({
                'order': order,
                'customer': None,
                'customer_name': order.customer_name,
                'mobile_number': order.mobile_number,
            })
    
    # Convert to list and sort by most recent order
    grouped_orders = []
    for key, order_list in customer_orders.items():
        # Sort orders within group by most recent
        order_list.sort(key=lambda x: x['order'].created_at, reverse=True)
        grouped_orders.append({
            'customer': order_list[0]['customer'],
            'customer_name': order_list[0]['customer_name'],
            'mobile_number': order_list[0]['mobile_number'],
            'orders': order_list,
            'last_order_date': order_list[0]['order'].created_at,
            'total_orders': len(order_list),
            'total_due': sum(o['order'].due_amount for o in order_list),
        })
    
    # Sort groups by most recent order
    grouped_orders.sort(key=lambda x: x['last_order_date'], reverse=True)
    
    # Pagination
    paginator = Paginator(grouped_orders, per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'grouped_orders': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'delivery_status_filter': delivery_status_filter,
        'date_filter': date_filter,
        'from_date': from_date,
        'to_date': to_date,
        'payment_status': payment_status,
        'per_page': per_page,
    }
    return render(request, 'admin_panel/order_list.html', context)


@login_required
def order_create(request):
    """নতুন অর্ডার তৈরি - একাধিক পণ্য সাপোর্ট"""
    try:
        products = InventoryProduct.objects.filter(is_active=True, stock_quantity__gt=0).order_by('name')
        customers = Customer.objects.all().order_by('name')
        products_json = json.dumps([
            {
                'id': p.pk,
                'name': p.name,
                'price': float(p.price_per_unit),
                'unit': p.get_unit_display(),
                'stock': float(p.stock_quantity),
            }
            for p in products
        ])
        customers_json = json.dumps([
            {
                'id': c.pk,
                'name': c.name,
                'mobile': c.mobile_number,
                'address': c.address or '',
            }
            for c in customers
        ])
    except Exception as e:
        messages.error(request, f'❌ ডেটা লোড করতে ত্রুটি: {str(e)}')
        return redirect('order_list')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        items_json_str = request.POST.get('items_json', '[]')

        try:
            items_data = json.loads(items_json_str)
        except (json.JSONDecodeError, ValueError):
            items_data = []

        if not items_data:
            messages.error(request, '❌ কমপক্ষে একটি পণ্য যোগ করুন!')
        elif form.is_valid():
            try:
                # Validate items and calculate total
                total_price = Decimal('0')
                validated_items = []
                for item in items_data:
                    product_name = item.get('product_name', '').strip()
                    quantity = Decimal(str(item.get('quantity', 0)))
                    unit_price = Decimal(str(item.get('unit_price', 0)))
                    
                    if not product_name:
                        raise ValueError("পণ্যের নাম লিখুন")
                    if quantity <= 0:
                        raise ValueError(f"{product_name}: পরিমাণ ০-এর বেশি হতে হবে")
                    if unit_price <= 0:
                        raise ValueError(f"{product_name}: মূল্য ০-এর বেশি হতে হবে")
                    
                    # Check stock availability for inventory products
                    try:
                        inventory_product = InventoryProduct.objects.filter(name__iexact=product_name).first()
                        if inventory_product:
                            if inventory_product.stock_quantity < quantity:
                                raise ValueError(f"{product_name}: স্টক অপর্যাপ্ত! বর্তমান স্টক: {inventory_product.stock_quantity} {inventory_product.get_unit_display()}")
                    except:
                        pass  # If no matching inventory product found, skip stock check
                    
                    item_total = quantity * unit_price
                    total_price += item_total
                    
                    validated_items.append({
                        'product_name': product_name,
                        'product_description': item.get('product_description', ''),
                        'quantity': quantity,
                        'unit_price': unit_price,
                    })

                # Save order
                order = form.save(commit=False)
                order.total_price = total_price
                
                # Link to customer if customer_id is provided
                customer_id = request.POST.get('customer_id')
                customer_name = request.POST.get('customer_name', '').strip()
                mobile_number = request.POST.get('mobile_number', '').strip()
                
                if customer_id:
                    try:
                        customer = Customer.objects.get(pk=customer_id)
                        order.customer = customer
                    except Customer.DoesNotExist:
                        pass
                elif customer_name and mobile_number:
                    # Automatically create customer if name and mobile are provided
                    # Clean mobile number
                    clean_mobile = ''.join(c for c in mobile_number if c.isdigit())
                    if clean_mobile and len(clean_mobile) >= 11:
                        customer, created = Customer.objects.get_or_create(
                            mobile_number=clean_mobile,
                            defaults={
                                'name': customer_name.strip().title(),
                                'address': ''
                            }
                        )
                        order.customer = customer
                
                order.save()

                # Create OrderItem records and update stock
                for item_data in validated_items:
                    OrderItem.objects.create(
                        order=order,
                        product_name=item_data['product_name'],
                        product_description=item_data['product_description'],
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                    )
                    
                    # Deduct stock from inventory
                    try:
                        inventory_product = InventoryProduct.objects.filter(name__iexact=item_data['product_name']).first()
                        if inventory_product:
                            inventory_product.remove_stock(item_data['quantity'])
                    except:
                        pass  # If no matching inventory product, skip stock update

                messages.success(request, f'✅ অর্ডার #{order.pk} সফলভাবে তৈরি হয়েছে!')
                return redirect('order_list')
            except ValueError as e:
                messages.error(request, f'❌ {str(e)}')
    else:
        form = OrderForm()

    context = {
        'form': form,
        'products_json': products_json,
        'customers_json': customers_json,
    }
    return render(request, 'admin_panel/order_form.html', context)


@login_required
def order_edit(request, pk):
    """অর্ডার সম্পাদনা - একাধিক পণ্য"""
    order = get_object_or_404(Order, pk=pk)

    try:
        products = InventoryProduct.objects.filter(is_active=True)
        products_json = json.dumps([
            {
                'id': p.pk,
                'name': p.name,
                'price': float(p.price_per_unit),
                'unit': p.get_unit_display(),
                'stock': float(p.stock_quantity),
            }
            for p in products
        ])
    except Exception as e:
        messages.error(request, f'❌ পণ্য ডেটা লোড করতে ত্রুটি: {str(e)}')
        return redirect('order_list')

    # Build existing items for template pre-population
    existing_items = [
        {
            'product_name': item.product_name,
            'product_description': item.product_description or '',
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
        }
        for item in order.items.all()
    ]

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        items_json_str = request.POST.get('items_json', '[]')

        try:
            items_data = json.loads(items_json_str)
        except (json.JSONDecodeError, ValueError):
            items_data = []

        if not items_data:
            messages.error(request, '❌ কমপক্ষে একটি পণ্য যোগ করুন!')
        elif form.is_valid():
            try:
                # Validate items and calculate total
                total_price = Decimal('0')
                validated_items = []
                for item in items_data:
                    product_name = item.get('product_name', '').strip()
                    quantity = Decimal(str(item.get('quantity', 0)))
                    unit_price = Decimal(str(item.get('unit_price', 0)))
                    
                    if not product_name:
                        raise ValueError("পণ্যের নাম লিখুন")
                    if quantity <= 0:
                        raise ValueError(f"{product_name}: পরিমাণ ০-এর বেশি হতে হবে")
                    if unit_price <= 0:
                        raise ValueError(f"{product_name}: মূল্য ০-এর বেশি হতে হবে")
                    
                    item_total = quantity * unit_price
                    total_price += item_total
                    
                    validated_items.append({
                        'product_name': product_name,
                        'product_description': item.get('product_description', ''),
                        'quantity': quantity,
                        'unit_price': unit_price,
                    })

                # Update order: lock original order_date, allow delivery_date update
                order_instance = form.save(commit=False)
                order_instance.total_price = total_price

                # অর্ডার নেওয়ার মূল তারিখ সবসময় অপরিবর্তিত থাকবে
                order_instance.order_date = order.order_date

                # ডেলিভারির তারিখ আপডেট করা যাবে (না দিলে পুরোনোই থাকবে)
                new_delivery_date = form.cleaned_data.get('delivery_date')
                if new_delivery_date:
                    order_instance.delivery_date = new_delivery_date
                else:
                    order_instance.delivery_date = order.delivery_date

                order_instance.save()

                # Delete old items and create new ones
                order.items.all().delete()
                for item_data in validated_items:
                    OrderItem.objects.create(
                        order=order,
                        product_name=item_data['product_name'],
                        product_description=item_data['product_description'],
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                    )

                messages.success(request, '✅ অর্ডার সফলভাবে আপডেট হয়েছে!')
                return redirect('order_list')
            except ValueError as e:
                messages.error(request, f'❌ {str(e)}')
    else:
        form = OrderForm(instance=order)

    customers = Customer.objects.all().order_by('name')
    customers_json = json.dumps([
        {
            'id': c.pk,
            'name': c.name,
            'mobile': c.mobile_number,
            'address': c.address or '',
        }
        for c in customers
    ])
    
    context = {
        'form': form,
        'order': order,
        'products_json': products_json,
        'customers_json': customers_json,
        'edit_items_json': json.dumps(existing_items),
    }
    return render(request, 'admin_panel/order_form.html', context)


@login_required
def order_delete(request, pk):
    """অর্ডার মুছে ফেলা"""
    order = get_object_or_404(Order, pk=pk)
    
    # Restore stock for each item before deleting
    for item in order.items.all():
        try:
            inventory_product = InventoryProduct.objects.filter(name__iexact=item.product_name).first()
            if inventory_product:
                inventory_product.add_stock(item.quantity)
        except:
            pass  # If no matching inventory product, skip stock restore
    
    order.delete()
    messages.success(request, 'অর্ডার মুছে ফেলা হয়েছে এবং স্টক পুনরুদ্ধার করা হয়েছে!')
    return redirect('order_list')


@login_required
def order_complete(request, pk):
    """অর্ডার সম্পন্ন করা এবং ডেলিভার করা"""
    order = get_object_or_404(Order, pk=pk)
    order.status = 'completed'
    order.delivery_status = 'delivered'  # Mark as delivered when completing
    order.save()
    messages.success(request, '✅ অর্ডার সম্পন্ন এবং ডেলিভার করা হয়েছে!')
    return redirect('completed_order_list')


@login_required
def completed_order_list(request):
    """সম্পন্ন এবং ডেলিভার করা অর্ডার তালিকা"""
    search_query = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)

    # শুধু সম্পন্ন এবং ডেলিভার করা অর্ডার
    orders = Order.objects.filter(status='completed', delivery_status='delivered').order_by('-created_at')

    if search_query:
        orders = orders.filter(
            Q(customer_name__icontains=search_query) |
            Q(mobile_number__icontains=search_query) |
            Q(items__product_name__icontains=search_query)
        ).distinct()

    paginator = Paginator(orders, 15)
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'admin_panel/completed_order_list.html', context)


@login_required
def order_voucher(request, pk):
    """অর্ডার ভাউচার/ইনভয়েস"""
    order = get_object_or_404(Order, pk=pk)
    shop_info = ShopInfo.objects.first()

    # Get other due orders from same customer
    other_due_orders = []
    if order.customer:
        other_due_orders = Order.objects.filter(
            customer=order.customer,
            due_amount__gt=0
        ).exclude(pk=order.pk).order_by('-created_at')
    else:
        other_due_orders = Order.objects.filter(
            customer_name=order.customer_name,
            mobile_number=order.mobile_number,
            due_amount__gt=0
        ).exclude(pk=order.pk).order_by('-created_at')

    # Calculate total due from other orders
    other_due_total = sum(o.due_amount for o in other_due_orders)
    
    # Calculate total due from all orders (current + other)
    total_due_all = order.due_amount + other_due_total

    context = {
        'order': order,
        'shop_info': shop_info,
        'other_due_orders': other_due_orders,
        'other_due_total': other_due_total,
        'total_due_all': total_due_all,
    }
    return render(request, 'admin_panel/voucher.html', context)


@login_required
def customer_combined_voucher(request, customer_pk):
    """সকল অর্ডারের জন্য একটি সম্মিলিত ভাউচার"""
    customer = get_object_or_404(Customer, pk=customer_pk)
    shop_info = ShopInfo.objects.first()
    
    # Get all orders for this customer
    all_orders = Order.objects.filter(customer=customer).order_by('order_date')
    
    if not all_orders.exists():
        messages.error(request, '❌ এই ক্রেতার কোনো অর্ডার নেই!')
        return redirect('customer_detail', pk=customer_pk)
    
    # Collect all items from all orders, grouped by order
    all_items = []
    total_price = Decimal('0')
    total_paid = Decimal('0')
    total_due = Decimal('0')
    
    for order in all_orders:
        for item in order.items.all():
            all_items.append({
                'order_id': order.pk,
                'order_date': order.order_date,
                'product_name': item.product_name,
                'product_description': item.product_description,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'item_total': item.quantity * item.unit_price,
            })
        
        total_price += order.total_price
        total_paid += order.cash_paid
        total_due += order.due_amount
    
    # Calculate discount if any
    total_discount = Decimal('0')
    for order in all_orders:
        total_discount += order.discount_amount
    
    # Group items by order for template
    grouped_items = []
    current_order_id = None
    for item in all_items:
        if item['order_id'] != current_order_id:
            current_order_id = item['order_id']
            grouped_items.append({
                'is_header': True,
                'order_id': item['order_id'],
                'order_date': item['order_date'],
            })
        grouped_items.append({
            'is_header': False,
            **item
        })
    
    context = {
        'customer': customer,
        'shop_info': shop_info,
        'all_orders': all_orders,
        'all_items': all_items,
        'grouped_items': grouped_items,
        'total_price': total_price,
        'total_paid': total_paid,
        'total_due': total_due,
        'total_discount': total_discount,
        'order_count': all_orders.count(),
    }
    return render(request, 'admin_panel/combined_voucher.html', context)


# ==================== ক্রেতা ব্যবস্থাপনা (Customer Management) ====================

@login_required
def customer_list_new(request):
    """ক্রেতা তালিকা - কাস্টম অর্ডারের জন্য"""
    search_query = request.GET.get('search', '')
    due_filter = request.GET.get('due_filter', '')
    sort_by = request.GET.get('sort_by', '-created_at')
    page_number = request.GET.get('page', 1)
    
    customers = Customer.objects.all().annotate(
        total_orders=Count('orders'),
        total_price=Sum('orders__total_price'),
        total_due=Sum('orders__due_amount')
    )
    
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(mobile_number__icontains=search_query)
        )
    
    # Filter by due payment
    if due_filter == 'with_due':
        customers = customers.filter(total_due__gt=0)
    elif due_filter == 'no_due':
        customers = customers.filter(Q(total_due__lte=0) | Q(total_due__isnull=True))
    
    # Sort
    if sort_by == 'name':
        customers = customers.order_by('name')
    elif sort_by == '-name':
        customers = customers.order_by('-name')
    elif sort_by == 'due':
        customers = customers.order_by('-total_due')
    elif sort_by == 'orders':
        customers = customers.order_by('-total_orders')
    elif sort_by == 'price':
        customers = customers.order_by('-total_price')
    else:
        customers = customers.order_by(sort_by)
    
    paginator = Paginator(customers, 20)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customers': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'due_filter': due_filter,
        'sort_by': sort_by,
    }
    return render(request, 'admin_panel/customer_list_new.html', context)


@login_required
def customer_create(request):
    """নতুন ক্রেতা তৈরি"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'✅ ক্রেতা {customer.name} সফলভাবে যোগ করা হয়েছে!')
            return redirect('customer_detail', pk=customer.pk)
    else:
        form = CustomerForm()
    
    context = {'form': form}
    return render(request, 'admin_panel/customer_form.html', context)


@login_required
def customer_edit(request, pk):
    """ক্রেতা সম্পাদনা"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ ক্রেতা {customer.name} সফলভাবে আপডেট করা হয়েছে!')
            return redirect('customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    
    context = {'form': form, 'customer': customer}
    return render(request, 'admin_panel/customer_form.html', context)


@login_required
def customer_detail(request, pk):
    """ক্রেতা বিস্তারিত - সব অর্ডার সহ"""
    customer = get_object_or_404(Customer, pk=pk)
    
    # Get all orders for this customer
    orders = customer.orders.all().order_by('-created_at')
    
    # Statistics
    total_orders = orders.count()
    total_price = sum(order.total_price for order in orders)
    total_paid = sum(order.cash_paid for order in orders)
    total_due = sum(order.due_amount for order in orders)
    
    # Delivery status counts
    delivered_count = orders.filter(delivery_status='delivered').count()
    pending_count = orders.filter(delivery_status='not_delivered').count()
    
    # Separate ongoing and completed orders
    ongoing_orders = orders.exclude(status='completed')
    completed_orders = orders.filter(status='completed')
    
    context = {
        'customer': customer,
        'orders': orders,
        'ongoing_orders': ongoing_orders,
        'completed_orders': completed_orders,
        'total_orders': total_orders,
        'total_price': total_price,
        'total_paid': total_paid,
        'total_due': total_due,
        'delivered_count': delivered_count,
        'pending_count': pending_count,
    }
    return render(request, 'admin_panel/customer_detail.html', context)


@login_required
def customer_detail_redirect(request, pk):
    """Redirect to transactions app customer detail by looking up mobile number"""
    from transactions.models import Customer as TransactionCustomer
    
    # Get the shop customer
    shop_customer = get_object_or_404(Customer, pk=pk)
    
    # Find the corresponding transaction customer by mobile number
    try:
        transaction_customer = TransactionCustomer.objects.get(mobile_number=shop_customer.mobile_number)
        # Redirect to the transactions app customer detail page
        return redirect('transactions:customer_detail', pk=transaction_customer.pk)
    except TransactionCustomer.DoesNotExist:
        # If not found in transactions app, show the old shop app detail page
        return redirect('customer_detail', pk=pk)


@login_required
def customer_delete(request, pk):
    """ক্রেতা মুছে ফেলা"""
    customer = get_object_or_404(Customer, pk=pk)
    
    # Check if customer has orders
    if customer.orders.exists():
        messages.error(request, f'❌ এই ক্রেতার {customer.orders.count()}টি অর্ডার আছে। মুছে ফেলা যাবে না!')
        return redirect('customer_detail', pk=customer.pk)
    
    customer.delete()
    messages.success(request, '✅ ক্রেতা সফলভাবে মুছে ফেলা হয়েছে!')
    return redirect('customer_list_new')


@login_required
def customer_deposit_create(request, customer_pk):
    """গ্রাহক জমা যোগ করা"""
    customer = get_object_or_404(Customer, pk=customer_pk)
    
    if request.method == 'POST':
        form = CustomerDepositForm(request.POST)
        if form.is_valid():
            deposit = form.save(commit=False)
            deposit.customer = customer
            deposit.transaction_type = 'deposit'
            deposit.save()
            messages.success(request, f'✅ ৳{deposit.amount} জমা সফলভাবে যোগ করা হয়েছে!')
            return redirect('customer_detail', pk=customer_pk)
    else:
        form = CustomerDepositForm()
    
    context = {
        'form': form,
        'customer': customer,
        'page_title': f'{customer.name} - জমা যোগ করুন',
    }
    return render(request, 'admin_panel/customer_deposit_form.html', context)


@login_required
def customer_deposit_list(request, customer_pk):
    """গ্রাহক জমার ইতিহাস"""
    customer = get_object_or_404(Customer, pk=customer_pk)
    deposits = customer.deposits.all().order_by('-created_at')
    
    context = {
        'customer': customer,
        'deposits': deposits,
        'page_title': f'{customer.name} - জমার ইতিহাস',
    }
    return render(request, 'admin_panel/customer_deposit_list.html', context)


@login_required
def customer_deposit_edit(request, pk):
    """গ্রাহক জমা সম্পাদনা"""
    deposit = get_object_or_404(CustomerDeposit, pk=pk)
    customer = deposit.customer
    
    if request.method == 'POST':
        form = CustomerDepositForm(request.POST, instance=deposit)
        if form.is_valid():
            # Calculate the difference to update customer balance
            old_amount = deposit.amount
            new_amount = form.cleaned_data['amount']
            difference = new_amount - old_amount
            
            # Update the deposit
            updated_deposit = form.save(commit=False)
            updated_deposit.amount = new_amount
            updated_deposit.save()
            
            # Update customer balance with the difference
            customer.deposit_balance += difference
            customer.save()
            
            messages.success(request, f'✅ জমা সফলভাবে আপডেট করা হয়েছে!')
            return redirect('customer_deposit_list', customer_pk=customer.pk)
    else:
        form = CustomerDepositForm(instance=deposit)
    
    context = {
        'form': form,
        'customer': customer,
        'deposit': deposit,
        'page_title': f'{customer.name} - জমা সম্পাদনা',
    }
    return render(request, 'admin_panel/customer_deposit_form.html', context)


@login_required
def customer_deposit_delete(request, pk):
    """গ্রাহক জমা মুছে ফেলা"""
    deposit = get_object_or_404(CustomerDeposit, pk=pk)
    customer = deposit.customer
    amount = deposit.amount
    transaction_type = deposit.transaction_type
    
    if request.method == 'POST':
        # Revert the balance change
        if transaction_type == 'deposit':
            customer.deposit_balance -= amount
        else:  # deduct
            customer.deposit_balance += amount
        
        customer.save()
        deposit.delete()
        
        messages.success(request, f'✅ জমা সফলভাবে মুছে ফেলা হয়েছে!')
        return redirect('customer_deposit_list', customer_pk=customer.pk)
    
    context = {
        'deposit': deposit,
        'customer': customer,
        'page_title': f'{customer.name} - জমা মুছে ফেলা',
    }
    return render(request, 'admin_panel/customer_deposit_delete.html', context)


@login_required
def customer_statement(request, pk):
    """ক্রেতার লেনদেনের বিবরণ - ব্যাংক স্টেটমেন্ট স্টাইলে"""
    from datetime import datetime
    
    customer = get_object_or_404(Customer, pk=pk)
    shop_info = ShopInfo.objects.first()
    
    # Get date filters from request
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    
    # Parse dates or use defaults
    from_date_obj = None
    to_date_obj = None
    
    if from_date:
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
        except ValueError:
            from_date_obj = None
    
    if to_date:
        try:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
        except ValueError:
            to_date_obj = None
    
    # Get all orders for this customer
    orders = customer.orders.all().order_by('order_date', 'created_at')
    
    # Apply date filters if provided
    if from_date_obj:
        orders = orders.filter(order_date__gte=from_date_obj)
    if to_date_obj:
        orders = orders.filter(order_date__lte=to_date_obj)
    
    # Build transaction list
    transactions = []
    running_balance = Decimal('0')
    
    for order in orders:
        # Add order as a debit (amount due)
        product_names = []
        if hasattr(order, 'items') and order.items.exists():
            product_names = [item.product_name for item in order.items.all()]
        elif hasattr(order, 'product') and order.product:
            product_names = [order.product.name]
        
        description = ', '.join(product_names) if product_names else 'অর্ডার'
        if len(description) > 50:
            description = description[:47] + '...'
        
        transactions.append({
            'type': 'order',
            'date': order.order_date if order.order_date else order.created_at.date(),
            'description': description,
            'debit': order.total_price,
            'credit': Decimal('0'),
            'balance': None,
            'order': order,
        })
        
        # Add payments as credits (with date filtering)
        order_payments = order.payments.all()
        if from_date_obj:
            order_payments = order_payments.filter(payment_date__gte=from_date_obj)
        if to_date_obj:
            order_payments = order_payments.filter(payment_date__lte=to_date_obj)
            
        for payment in order_payments.order_by('payment_date'):
            clean_notes = payment.notes.replace('প্রাথমিক পেমেন্ট (মাইগ্রেটেড)', '').strip() if payment.notes else ''
            description = 'পেমেন্ট'
            if clean_notes:
                description += f' ({clean_notes})'
            
            transactions.append({
                'type': 'payment',
                'date': payment.payment_date,
                'description': description,
                'debit': Decimal('0'),
                'credit': payment.amount,
                'balance': None,
                'payment': payment,
            })
    
    # Sort transactions by date
    transactions.sort(key=lambda x: (x['date'], x['type'] == 'payment'))
    
    # Calculate running balance
    for txn in transactions:
        running_balance += txn['debit'] - txn['credit']
        txn['balance'] = running_balance
    
    # Calculate totals
    total_debit = sum(t['debit'] for t in transactions)
    total_credit = sum(t['credit'] for t in transactions)
    current_due = total_debit - total_credit
    
    context = {
        'customer': customer,
        'shop_info': shop_info,
        'transactions': transactions,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'current_due': current_due,
        'from_date': from_date,
        'to_date': to_date,
        'from_date_obj': from_date_obj,
        'to_date_obj': to_date_obj,
        'now': datetime.now(),
    }
    
    return render(request, 'admin_panel/customer_statement.html', context)

@login_required
def order_create_for_customer(request, customer_pk):
    """নির্দিষ্ট ক্রেতার জন্য নতুন অর্ডার তৈরি"""
    customer = get_object_or_404(Customer, pk=customer_pk)
    
    try:
        products = InventoryProduct.objects.filter(is_active=True, stock_quantity__gt=0).order_by('name')
        products_json = json.dumps([
            {
                'id': p.pk,
                'name': p.name,
                'price': float(p.price_per_unit),
                'unit': p.get_unit_display(),
                'stock': float(p.stock_quantity),
            }
            for p in products
        ])
    except Exception as e:
        messages.error(request, f'❌ পণ্য ডেটা লোড করতে ত্রুটি: {str(e)}')
        return redirect('customer_detail', pk=customer_pk)

    if request.method == 'POST':
        form = OrderForm(request.POST)
        items_json_str = request.POST.get('items_json', '[]')

        try:
            items_data = json.loads(items_json_str)
        except (json.JSONDecodeError, ValueError):
            items_data = []

        if not items_data:
            messages.error(request, '❌ কমপক্ষে একটি পণ্য যোগ করুন!')
        elif not form.is_valid():
            # Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'❌ {field}: {error}')
        else:
            try:
                # Validate items and calculate total
                total_price = Decimal('0')
                validated_items = []
                for item in items_data:
                    product_name = item.get('product_name', '').strip()
                    quantity = Decimal(str(item.get('quantity', 0)))
                    unit_price = Decimal(str(item.get('unit_price', 0)))
                    discount_percentage = Decimal(str(item.get('discount_percentage', 0)))
                    
                    if not product_name:
                        raise ValueError("পণ্যের নাম লিখুন")
                    if quantity <= 0:
                        raise ValueError(f"{product_name}: পরিমাণ ০-এর বেশি হতে হবে")
                    if unit_price <= 0:
                        raise ValueError(f"{product_name}: মূল্য ০-এর বেশি হতে হবে")
                    
                    # Check stock availability for inventory products
                    try:
                        inventory_product = InventoryProduct.objects.filter(name__iexact=product_name).first()
                        if inventory_product:
                            if inventory_product.stock_quantity < quantity:
                                raise ValueError(f"{product_name}: স্টক অপর্যাপ্ত! বর্তমান স্টক: {inventory_product.stock_quantity} {inventory_product.get_unit_display()}")
                    except:
                        pass  # If no matching inventory product found, skip stock check
                    
                    item_total = quantity * unit_price
                    total_price += item_total
                    
                    validated_items.append({
                        'product_name': product_name,
                        'product_description': item.get('product_description', ''),
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'discount_percentage': discount_percentage,
                    })

                # Save order with customer
                order = form.save(commit=False)
                order.customer = customer
                order.customer_name = customer.name
                order.mobile_number = customer.mobile_number
                order.total_price = total_price
                order.save()

                # Create OrderItem records and update stock
                for item_data in validated_items:
                    OrderItem.objects.create(
                        order=order,
                        product_name=item_data['product_name'],
                        product_description=item_data['product_description'],
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        discount_percentage=item_data['discount_percentage'],
                    )
                    
                    # Deduct stock from inventory
                    try:
                        inventory_product = InventoryProduct.objects.filter(name__iexact=item_data['product_name']).first()
                        if inventory_product:
                            inventory_product.remove_stock(item_data['quantity'])
                    except:
                        pass  # If no matching inventory product, skip stock update

                messages.success(request, f'✅ {customer.name}-এর জন্য অর্ডার #{order.pk} সফলভাবে তৈরি হয়েছে!')
                return redirect('customer_detail', pk=customer.pk)
            except ValueError as e:
                messages.error(request, f'❌ {str(e)}')
    else:
        form = OrderForm(initial={
            'customer_name': customer.name,
            'mobile_number': customer.mobile_number,
            'order_date': timezone.now().date(),
            'delivery_date': (timezone.now() + timedelta(days=7)).date(),
            'status': 'pending',
            'delivery_status': 'not_delivered',
            'discount_percentage': 0,
        })
        # Make customer fields readonly
        form.fields['customer_name'].widget.attrs['readonly'] = True
        form.fields['customer_name'].widget.attrs['style'] = 'background-color: #f5f5f5;'
        form.fields['mobile_number'].widget.attrs['readonly'] = True
        form.fields['mobile_number'].widget.attrs['style'] = 'background-color: #f5f5f5;'
        
        # Ensure status field shows the default value
        form.fields['status'].initial = 'pending'
        form.fields['delivery_status'].initial = 'not_delivered'

    context = {
        'form': form,
        'products_json': products_json,
        'customer': customer,
    }
    return render(request, 'admin_panel/order_form_for_customer.html', context)


# ==================== ইনভেন্টরি পণ্য ব্যবস্থাপনা ====================

@login_required
def inventory_product_list(request):
    """ইনভেন্টরি পণ্য তালিকা"""
    search_query = request.GET.get('search', '')
    stock_filter = request.GET.get('stock_filter', '')
    page_number = request.GET.get('page', 1)
    show_all = request.GET.get('all', '') == '1'

    products = InventoryProduct.objects.all()

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply stock filter
    if stock_filter == 'zero':
        products = products.filter(stock_quantity=0)
    elif stock_filter == 'low':
        products = products.filter(stock_quantity__gt=0, stock_quantity__lte=10)
    elif stock_filter == 'in_stock':
        products = products.filter(stock_quantity__gt=0)
    elif stock_filter == 'high':
        products = products.filter(stock_quantity__gt=10)

    # Show all products if "all=1" parameter is present
    if show_all:
        paginator = Paginator(products, products.count())
        page_obj = paginator.get_page(1)
    else:
        paginator = Paginator(products, 15)
        page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'stock_filter': stock_filter,
    }
    return render(request, 'admin_panel/inventory_product_list.html', context)


@login_required
def bulk_price_update(request):
    """বাল্ক পণ্যের মূল্য বৃদ্ধি"""
    search_query = request.GET.get('search', '')
    products = InventoryProduct.objects.all().order_by('name')
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if request.method == 'POST':
        selected_products = request.POST.getlist('selected_products')
        increase_percentage = request.POST.get('increase_percentage')
        
        if not selected_products:
            messages.error(request, '❌ কমপক্ষে একটি পণ্য নির্বাচন করুন!')
        elif not increase_percentage:
            messages.error(request, '❌ বৃদ্ধির শতাংশ দিন!')
        else:
            try:
                percentage = float(increase_percentage)
                if percentage <= 0:
                    messages.error(request, '❌ শতাংশ ০-এর বেশি হতে হবে!')
                else:
                    from decimal import Decimal
                    updated_count = 0
                    for product_id in selected_products:
                        try:
                            product = InventoryProduct.objects.get(pk=product_id)
                        except InventoryProduct.DoesNotExist:
                            continue
                        old_price = product.price_per_unit
                        new_price = product.price_per_unit * (Decimal('1') + Decimal(str(percentage)) / Decimal('100'))
                        product.price_per_unit = new_price
                        product.save()
                        PriceHistory.objects.create(
                            product=product,
                            old_price=old_price,
                            new_price=new_price,
                            change_percentage=Decimal(str(percentage)),
                            is_bulk=True,
                        )
                        updated_count += 1
                    
                    messages.success(request, f'✅ {updated_count} টি পণ্যের মূল্য {percentage}% বৃদ্ধি করা হয়েছে!')
                    return redirect('inventory_product_list')
            except ValueError:
                messages.error(request, '❌ সঠিক শতাংশ দিন!')
    
    context = {
        'products': products,
        'search_query': search_query,
    }
    return render(request, 'admin_panel/bulk_price_update.html', context)


@login_required
def price_history_list(request):
    """মূল্য পরিবর্তনের ইতিহাস - রিভার্ট বাটন সহ"""
    search_query = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)
    
    history = PriceHistory.objects.all().select_related('product')
    
    if search_query:
        history = history.filter(product__name__icontains=search_query)
    
    paginator = Paginator(history, 20)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'history': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'admin_panel/price_history_list.html', context)


@login_required
def price_history_revert(request, pk):
    """মূল্য পরিবর্তন রিভার্ট করুন"""
    price_change = get_object_or_404(PriceHistory, pk=pk)
    product = price_change.product
    
    # Revert to old price
    product.price_per_unit = price_change.old_price
    product.save()
    
    # Record the revert as a new history entry
    PriceHistory.objects.create(
        product=product,
        old_price=price_change.new_price,
        new_price=price_change.old_price,
        change_percentage=price_change.change_percentage * -1,
        is_bulk=False,
    )
    
    messages.success(request, f'✅ {product.name}-এর মূল্য ৳{price_change.new_price} থেকে ৳{price_change.old_price}-এ ফিরিয়ে নেওয়া হয়েছে!')
    return redirect('price_history_list')


@login_required
def price_history_bulk_revert(request):
    """একাধিক মূল্য পরিবর্তন বাল্ক রিভার্ট"""
    if request.method != 'POST':
        messages.error(request, '❌ অনুগ্রহ করে রিভার্ট করার জন্য আইটেম নির্বাচন করুন')
        return redirect('price_history_list')

    ids = request.POST.getlist('selected')
    if not ids:
        messages.error(request, '❌ কোনো রেকর্ড নির্বাচন করা হয়নি')
        return redirect('price_history_list')

    reverted = 0
    for pk in ids:
        try:
            price_change = PriceHistory.objects.get(pk=pk)
            product = price_change.product
            # Revert to old price
            product.price_per_unit = price_change.old_price
            product.save()
            # Record the revert as a new history entry
            PriceHistory.objects.create(
                product=product,
                old_price=price_change.new_price,
                new_price=price_change.old_price,
                change_percentage=price_change.change_percentage * -1,
                is_bulk=False,
            )
            reverted += 1
        except PriceHistory.DoesNotExist:
            continue

    messages.success(request, f'✅ নির্বাচিত {reverted}টি রেকর্ড সফলভাবে রিভার্ট করা হয়েছে')
    return redirect('price_history_list')


@login_required
def inventory_product_create(request):
    """নতুন ইনভেন্টরি পণ্য তৈরি"""
    if request.method == 'POST':
        form = InventoryProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ পণ্য সফলভাবে যোগ করা হয়েছে!')
            return redirect('inventory_product_list')
    else:
        form = InventoryProductForm()

    context = {'form': form}
    return render(request, 'admin_panel/inventory_product_form.html', context)


@login_required
def inventory_product_edit(request, pk):
    """ইনভেন্টরি পণ্য সম্পাদনা"""
    product = get_object_or_404(InventoryProduct, pk=pk)

    if request.method == 'POST':
        form = InventoryProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ পণ্য সফলভাবে আপডেট করা হয়েছে!')
            return redirect('inventory_product_list')
    else:
        form = InventoryProductForm(instance=product)

    context = {'form': form, 'product': product}
    return render(request, 'admin_panel/inventory_product_form.html', context)


@login_required
def inventory_product_delete(request, pk):
    """ইনভেন্টরি পণ্য মুছে ফেলা"""
    product = get_object_or_404(InventoryProduct, pk=pk)

    # চেক করুন এই পণ্যের কোনো বিক্রয় আছে কিনা
    invoice_count = Invoice.objects.filter(product=product).count()

    if invoice_count > 0:
        messages.error(request, f'❌ এই পণ্যটি মুছে ফেলা যাবে না! {invoice_count}টি ভাউচারে এই পণ্য ব্যবহার হয়েছে। পণ্যটি নিষ্ক্রিয় করতে চাইলে এডিট করুন।')
        return redirect('inventory_product_list')

    product.delete()
    messages.success(request, '✅ পণ্য সফলভাবে মুছে ফেলা হয়েছে!')
    return redirect('inventory_product_list')


@login_required
def stock_management(request, pk):
    """স্টক ব্যবস্থাপনা - স্টক যোগ/কমানো"""
    product = get_object_or_404(InventoryProduct, pk=pk)
    
    if request.method == 'POST':
        form = StockManagementForm(request.POST)
        if form.is_valid():
            operation_type = form.cleaned_data['operation_type']
            quantity = form.cleaned_data['quantity']
            notes = form.cleaned_data['notes']
            
            try:
                previous_quantity = product.stock_quantity
                
                if operation_type == 'add':
                    product.add_stock(quantity)
                    messages.success(request, f'✅ {quantity} {product.get_unit_display()} স্টক যোগ করা হয়েছে!')
                    # Record stock history
                    StockHistory.objects.create(
                        product=product,
                        operation='add',
                        quantity=quantity,
                        previous_quantity=previous_quantity,
                        new_quantity=product.stock_quantity,
                        notes=notes
                    )
                elif operation_type == 'remove':
                    product.remove_stock(quantity)
                    messages.success(request, f'✅ {quantity} {product.get_unit_display()} স্টক কমানো হয়েছে!')
                    # Record stock history
                    StockHistory.objects.create(
                        product=product,
                        operation='remove',
                        quantity=quantity,
                        previous_quantity=previous_quantity,
                        new_quantity=product.stock_quantity,
                        notes=notes
                    )
                
                return redirect('inventory_product_list')
            except ValueError as e:
                messages.error(request, f'❌ {str(e)}')
    else:
        form = StockManagementForm()
    
    context = {
        'form': form,
        'product': product,
        'operation_title': 'স্টক ব্যবস্থাপনা'
    }
    return render(request, 'admin_panel/stock_management.html', context)



# ==================== ইনভয়েস/ভাউচার ব্যবস্থাপনা ====================

@login_required
def invoice_list(request):
    """ইনভয়েস তালিকা - তারিখ ফিল্টার এবং কনফিগারেবল পেজিনেশন সহ"""
    search_query = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', '15')
    date_filter = request.GET.get('date_filter', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    payment_status = request.GET.get('payment_status', '')
    
    # Validate per_page
    try:
        per_page = int(per_page)
        if per_page not in [15, 50, 100, 200]:
            per_page = 15
    except ValueError:
        per_page = 15

    invoices = Invoice.objects.filter(is_latest=True)
    
    # Apply payment status filter
    if payment_status == 'paid':
        invoices = invoices.filter(due_amount=0)
    elif payment_status == 'due':
        invoices = invoices.filter(due_amount__gt=0)
    elif payment_status == 'partial':
        invoices = invoices.filter(paid_amount__gt=0, due_amount__gt=0)
    
    # Apply date filters
    today = timezone.now().date()
    
    if date_filter == 'today':
        invoices = invoices.filter(sale_date=today)
    elif date_filter == 'week':
        week_ago = today - timedelta(days=7)
        invoices = invoices.filter(sale_date__gte=week_ago)
    elif date_filter == 'month':
        month_ago = today - timedelta(days=30)
        invoices = invoices.filter(sale_date__gte=month_ago)
    elif date_filter == 'year':
        year_ago = today - timedelta(days=365)
        invoices = invoices.filter(sale_date__gte=year_ago)
    elif date_filter == 'custom' and from_date and to_date:
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            invoices = invoices.filter(sale_date__range=[from_date_obj, to_date_obj])
        except ValueError:
            pass
    
    # Apply search filter
    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(mobile_number__icontains=search_query)
        )
    
    # Order by date (newest first)
    invoices = invoices.order_by('-sale_date', '-created_at')

    paginator = Paginator(invoices, per_page)
    page_obj = paginator.get_page(page_number)
    
    # Calculate statistics
    total_count = invoices.count()
    total_amount = invoices.aggregate(total=Sum('total_amount'))['total'] or 0
    total_paid = invoices.aggregate(total=Sum('paid_amount'))['total'] or 0
    total_due = invoices.aggregate(total=Sum('due_amount'))['total'] or 0

    context = {
        'invoices': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'per_page': per_page,
        'date_filter': date_filter,
        'from_date': from_date,
        'to_date': to_date,
        'payment_status': payment_status,
        'total_count': total_count,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_due': total_due,
        'debug': True,  # Debug flag
    }
    print(f"DEBUG invoice_list: date_filter={date_filter}, per_page={per_page}, payment_status={payment_status}")  # Debug output
    return render(request, 'admin_panel/invoice_list.html', context)


@login_required
def invoice_create(request):
    """নতুন ইনভয়েস তৈরি - একাধিক পণ্য সাপোর্ট"""
    products = InventoryProduct.objects.filter(is_active=True, stock_quantity__gt=0).order_by('name')
    products_json = json.dumps([
        {
            'id': p.pk,
            'name': p.name,
            'price': float(p.price_per_unit),
            'unit': p.get_unit_display(),
            'stock': float(p.stock_quantity),
        }
        for p in products
    ])

    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        items_json_str = request.POST.get('items_json', '[]')

        try:
            items_data = json.loads(items_json_str)
        except (json.JSONDecodeError, ValueError):
            items_data = []

        if not items_data:
            messages.error(request, '❌ কমপক্ষে একটি পণ্য যোগ করুন!')
        elif form.is_valid():
            try:
                # Validate each item and compute grand subtotal (after per-item discount)
                grand_subtotal = Decimal('0')
                validated_items = []
                for item in items_data:
                    product = InventoryProduct.objects.get(pk=item['product_id'])
                    quantity = Decimal(str(item['quantity']))
                    disc_pct = Decimal(str(item.get('discount_percentage', 0)))
                    if quantity <= 0:
                        raise ValueError(f"{product.name}: পরিমাণ ০-এর বেশি হতে হবে")
                    if disc_pct < 0 or disc_pct > 100:
                        raise ValueError(f"{product.name}: ছাড় ০–১০০%-এর মধ্যে হতে হবে")
                    if product.stock_quantity < quantity:
                        raise ValueError(f"{product.name}: স্টক অপর্যাপ্ত! বর্তমান স্টক: {product.stock_quantity}")
                    unit_price = product.price_per_unit
                    gross = quantity * unit_price
                    item_discount = (gross * disc_pct) / 100
                    item_net = gross - item_discount
                    grand_subtotal += item_net
                    validated_items.append({
                        'product': product,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'discount_percentage': disc_pct,
                    })

                # Save invoice header (multi-item mode) with optional extra total discount
                invoice = form.save(commit=False)
                invoice.subtotal = grand_subtotal
                global_discount = form.cleaned_data.get('global_discount')
                if global_discount is None:
                    global_discount = Decimal('0')
                invoice.discount_percentage = global_discount
                invoice.save()

                # Create InvoiceItem rows and deduct stock
                for item in validated_items:
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        product=item['product'],
                        quantity=item['quantity'],
                        unit_price=item['unit_price'],
                        discount_percentage=item['discount_percentage'],
                    )
                    item['product'].stock_quantity -= item['quantity']
                    item['product'].save()

                messages.success(request, f'✅ ইনভয়েস {invoice.invoice_number} তৈরি হয়েছে!')
                return redirect('invoice_detail', pk=invoice.pk)
            except InventoryProduct.DoesNotExist:
                messages.error(request, '❌ পণ্য খুঁজে পাওয়া যায়নি!')
            except ValueError as e:
                messages.error(request, f'❌ {str(e)}')
    else:
        form = InvoiceForm()

    context = {'form': form, 'products_json': products_json}
    return render(request, 'admin_panel/invoice_form.html', context)


@login_required
def invoice_detail(request, pk):
    """ইনভয়েস বিস্তারিত"""
    invoice = get_object_or_404(Invoice, pk=pk)
    shop_info = ShopInfo.objects.first()
    
    # Calculate paid_amount: Payment records are source of truth if they exist
    # Otherwise use stored paid_amount (for initial payment)
    total_paid_from_payments = sum(p.amount for p in invoice.payments.all())
    if invoice.payments.exists():
        # Payment records exist - they are the source of truth
        if abs(float(invoice.paid_amount) - float(total_paid_from_payments)) > 0.01:
            # Update database if mismatch
            Invoice.objects.filter(pk=invoice.pk).update(
                paid_amount=total_paid_from_payments,
                due_amount=invoice.total_amount - total_paid_from_payments
            )
            invoice.refresh_from_db()
        display_paid = total_paid_from_payments
    else:
        # No Payment records - use stored paid_amount (initial payment from invoice creation)
        display_paid = invoice.paid_amount
    
    # Update invoice object for template display
    invoice.paid_amount = display_paid
    invoice.due_amount = invoice.total_amount - display_paid

    # সব ভার্সন দেখানো
    all_versions = []
    if invoice.original_invoice:
        all_versions = Invoice.objects.filter(
            Q(pk=invoice.original_invoice.pk) | Q(original_invoice=invoice.original_invoice)
        ).order_by('-created_at')
    else:
        all_versions = Invoice.objects.filter(
            Q(pk=invoice.pk) | Q(original_invoice=invoice)
        ).order_by('-created_at')

    context = {
        'invoice': invoice,
        'shop_info': shop_info,
        'all_versions': all_versions,
    }
    return render(request, 'admin_panel/invoice_detail.html', context)


@login_required
def invoice_edit(request, pk):
    """ইনভয়েস এডিট (নতুন ভার্সন তৈরি) - একাধিক পণ্য সাপোর্ট"""
    old_invoice = get_object_or_404(Invoice, pk=pk)

    products = InventoryProduct.objects.filter(is_active=True)
    products_json = json.dumps([
        {
            'id': p.pk,
            'name': p.name,
            'price': float(p.price_per_unit),
            'unit': p.get_unit_display(),
            'stock': float(p.stock_quantity),
        }
        for p in products
    ])

    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        items_json_str = request.POST.get('items_json', '[]')

        try:
            items_data = json.loads(items_json_str)
        except (json.JSONDecodeError, ValueError):
            items_data = []

        if not items_data:
            messages.error(request, '❌ কমপক্ষে একটি পণ্য যোগ করুন!')
        elif form.is_valid():
            try:
                # Validate & compute grand subtotal (after per-item discount)
                grand_subtotal = Decimal('0')
                validated_items = []
                for item in items_data:
                    product = InventoryProduct.objects.get(pk=item['product_id'])
                    quantity = Decimal(str(item['quantity']))
                    disc_pct = Decimal(str(item.get('discount_percentage', 0)))
                    if quantity <= 0:
                        raise ValueError(f"{product.name}: পরিমাণ ০-এর বেশি হতে হবে")
                    if disc_pct < 0 or disc_pct > 100:
                        raise ValueError(f"{product.name}: ছাড় ০–১০০%-এর মধ্যে হতে হবে")
                    unit_price = product.price_per_unit
                    gross = quantity * unit_price
                    item_discount = (gross * disc_pct) / 100
                    grand_subtotal += gross - item_discount
                    validated_items.append({
                        'product': product,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'discount_percentage': disc_pct,
                    })

                # Restore stock from old invoice
                if old_invoice.product:
                    old_invoice.product.stock_quantity += old_invoice.quantity
                    old_invoice.product.save()
                else:
                    for old_item in old_invoice.items.all():
                        old_item.product.stock_quantity += old_item.quantity
                        old_item.product.save()

                # Check stock availability for new items
                for item in validated_items:
                    if item['product'].stock_quantity < item['quantity']:
                        raise ValueError(f"{item['product'].name}: স্টক অপর্যাপ্ত! বর্তমান স্টক: {item['product'].stock_quantity}")

                # Create new invoice (with optional extra total discount on top of per-item discounts)
                new_invoice = form.save(commit=False)
                new_invoice.subtotal = grand_subtotal
                global_discount = form.cleaned_data.get('global_discount')
                if global_discount is None:
                    global_discount = Decimal('0')
                new_invoice.discount_percentage = global_discount
                # বিক্রয়ের তারিখ সবসময় মূল ইনভয়েসের মতোই থাকবে
                new_invoice.sale_date = old_invoice.sale_date
                new_invoice.original_invoice = old_invoice.original_invoice or old_invoice
                new_invoice.save()

                # Create items and deduct stock
                for item in validated_items:
                    InvoiceItem.objects.create(
                        invoice=new_invoice,
                        product=item['product'],
                        quantity=item['quantity'],
                        unit_price=item['unit_price'],
                        discount_percentage=item['discount_percentage'],
                    )
                    item['product'].stock_quantity -= item['quantity']
                    item['product'].save()

                # Mark old invoice as not latest
                Invoice.objects.filter(pk=old_invoice.pk).update(is_latest=False)

                messages.success(request, f'✅ নতুন ইনভয়েস {new_invoice.invoice_number} তৈরি হয়েছে! পুরাতন ইনভয়েস সংরক্ষিত আছে।')
                return redirect('invoice_detail', pk=new_invoice.pk)
            except InventoryProduct.DoesNotExist:
                messages.error(request, '❌ পণ্য খুঁজে পাওয়া যায়নি!')
            except ValueError as e:
                messages.error(request, f'❌ {str(e)}')
    else:
        form = InvoiceForm(initial={
            'customer_name': old_invoice.customer_name,
            'mobile_number': old_invoice.mobile_number,
            'paid_amount': old_invoice.paid_amount,
            'notes': old_invoice.notes,
            'sale_date': old_invoice.sale_date,
            'global_discount': old_invoice.discount_percentage,
        })

    # Build existing items for template pre-population (includes per-item discount)
    if old_invoice.items.exists():
        edit_items = [
            {
                'product_id': item.product_id,
                'product_name': item.product.name,
                'quantity': float(item.quantity),
                'unit_price': float(item.unit_price),
                'discount_percentage': float(item.discount_percentage),
                'unit': item.product.get_unit_display(),
            }
            for item in old_invoice.items.all()
        ]
    elif old_invoice.product:
        edit_items = [{
            'product_id': old_invoice.product_id,
            'product_name': old_invoice.product.name,
            'quantity': float(old_invoice.quantity),
            'unit_price': float(old_invoice.unit_price),
            'discount_percentage': float(old_invoice.discount_percentage),
            'unit': old_invoice.product.get_unit_display(),
        }]
    else:
        edit_items = []

    context = {
        'form': form,
        'old_invoice': old_invoice,
        'products_json': products_json,
        'edit_items_json': json.dumps(edit_items),
    }
    return render(request, 'admin_panel/invoice_form.html', context)


@login_required
def invoice_delete(request, pk):
    """ইনভয়েস/ভাউচার মুছে ফেলা"""
    invoice = get_object_or_404(Invoice, pk=pk)
    inv_number = invoice.invoice_number
    try:
        # স্টক ফেরত (বিক্রয় বাতিল হিসাবে)
        if invoice.product:
            # Single-product (old-style) invoice
            invoice.product.stock_quantity += invoice.quantity
            invoice.product.save()
        else:
            # Multi-item invoice
            for item in invoice.items.all():
                item.product.stock_quantity += item.quantity
                item.product.save()
        invoice.delete()
        messages.success(request, f'✅ ইনভয়েস {inv_number} মুছে ফেলা হয়েছে।')
    except Exception as e:
        messages.error(request, f'❌ মুছে ফেলতে ত্রুটি: {str(e)}')
    return redirect('invoice_list')


@login_required
def payment_create(request, invoice_pk):
    """নতুন পেমেন্ট যোগ করা - আংশিক পেমেন্ট"""
    invoice = get_object_or_404(Invoice, pk=invoice_pk)
    invoice.refresh_from_db()
    
    # Calculate current paid: stored paid_amount + sum of Payment records
    # This handles both initial paid_amount and subsequent Payment records
    total_paid_from_payments = sum(p.amount for p in invoice.payments.all())
    # If no Payment records exist, use stored paid_amount; otherwise use Payment records as source of truth
    if invoice.payments.exists():
        current_paid = total_paid_from_payments
    else:
        # No Payment records yet, use stored paid_amount (initial payment)
        current_paid = invoice.paid_amount
    
    current_due = invoice.total_amount - current_paid

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            try:
                payment = form.save(commit=False)
                payment.invoice = invoice
                payment_amount = payment.amount
                
                # Validate payment doesn't exceed due amount
                if payment_amount > current_due:
                    messages.error(request, f'❌ অতিরিক্ত পেমেন্ট! মোট মূল্য: ৳{invoice.total_amount}, ইতিমধ্যে পরিশোধিত: ৳{current_paid}, বাকি: ৳{current_due}। সর্বোচ্চ যুক্ত করতে পারেন: ৳{current_due}')
                    return redirect('payment_create', invoice_pk=invoice.pk)
                
                # If this is the first Payment and invoice has initial paid_amount, migrate it to Payment record
                # Check BEFORE saving the new payment
                if not invoice.payments.exists() and invoice.paid_amount > 0:
                    from shop.models import Payment as PaymentModel
                    PaymentModel.objects.create(
                        invoice=invoice,
                        amount=invoice.paid_amount,
                        payment_date=invoice.sale_date,
                        notes='প্রাথমিক পেমেন্ট (মাইগ্রেটেড)'
                    )
                    invoice.refresh_from_db()
                
                # Save the new payment
                payment.save()

                # Update invoice totals: sum all Payment records (includes initial + new payment)
                invoice.refresh_from_db()
                total_paid = sum(p.amount for p in invoice.payments.all())
                
                # Update invoice using update() to avoid triggering save() recalculation
                Invoice.objects.filter(pk=invoice.pk).update(
                    paid_amount=total_paid,
                    due_amount=invoice.total_amount - total_paid
                )

                messages.success(request, f'✅ পেমেন্ট ৳{payment.amount} সফলভাবে যোগ করা হয়েছে!')
                return redirect('invoice_detail', pk=invoice.pk)
            except Exception as e:
                messages.error(request, f'❌ ত্রুটি: {str(e)}')
    else:
        form = PaymentForm()
    
    # For display: use calculated values
    invoice.paid_amount = current_paid
    invoice.due_amount = current_due

    context = {
        'form': form,
        'invoice': invoice,
    }
    return render(request, 'admin_panel/payment_form.html', context)


@login_required
def payment_edit(request, pk):
    """Edit an existing Payment for an invoice.

    Keeps invoice.paid_amount and invoice.due_amount consistent and
    prevents overpayment when the amount is changed.
    """
    payment = get_object_or_404(Payment, pk=pk)
    invoice = payment.invoice

    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            updated_payment = form.save(commit=False)
            new_amount = updated_payment.amount

            # Sum of all other payments for this invoice
            other_total = sum(p.amount for p in invoice.payments.exclude(pk=payment.pk))
            max_allowed = invoice.total_amount - other_total

            if new_amount > max_allowed:
                messages.error(
                    request,
                    f'❌ অতিরিক্ত পেমেন্ট! সর্বোচ্চ পরিমাণ: ৳{max_allowed}',
                )
            else:
                # Save updated payment
                payment.amount = updated_payment.amount
                payment.payment_date = updated_payment.payment_date
                payment.notes = updated_payment.notes
                payment.save()

                # Recalculate invoice totals from all Payment records
                total_paid = sum(p.amount for p in invoice.payments.all())
                Invoice.objects.filter(pk=invoice.pk).update(
                    paid_amount=total_paid,
                    due_amount=invoice.total_amount - total_paid,
                )

                messages.success(request, '✅ পেমেন্ট সফলভাবে আপডেট করা হয়েছে!')
                return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = PaymentForm(instance=payment)

    # For display: use Payment records as source of truth
    invoice.refresh_from_db()
    total_paid = sum(p.amount for p in invoice.payments.all())
    if invoice.payments.exists():
        display_paid = total_paid
    else:
        display_paid = invoice.paid_amount

    invoice.paid_amount = display_paid
    invoice.due_amount = invoice.total_amount - display_paid

    context = {
        'form': form,
        'invoice': invoice,
        'payment': payment,
    }
    return render(request, 'admin_panel/payment_form.html', context)


@login_required
def payment_delete(request, pk):
    """Delete a Payment and update the parent invoice totals.

    Follows the same pattern as invoice_delete (GET with confirm in template).
    """
    payment = get_object_or_404(Payment, pk=pk)
    invoice = payment.invoice

    try:
        payment.delete()
        # Recalculate invoice totals from remaining Payment records
        total_paid = sum(p.amount for p in invoice.payments.all())
        Invoice.objects.filter(pk=invoice.pk).update(
            paid_amount=total_paid,
            due_amount=invoice.total_amount - total_paid,
        )
        messages.success(request, '✅ পেমেন্ট সফলভাবে মুছে ফেলা হয়েছে!')
    except Exception as e:
        messages.error(request, f'❌ পেমেন্ট মুছতে ত্রুটি: {str(e)}')

    return redirect('invoice_detail', pk=invoice.pk)


@login_required
def customer_profile(request, mobile_number):
    """কাস্টমার প্রোফাইল - একজন কাস্টমারের সব ভাউচার"""
    # মোবাইল নাম্বার থেকে শুধু সংখ্যা বের করা (স্পেস/ড্যাশ অপসারণ)
    clean_mobile = ''.join(filter(str.isdigit, mobile_number))

    # এই মোবাইল নাম্বারের সব ইনভয়েস (পুরাতন + নতুন সব)
    all_invoices = Invoice.objects.filter(
        mobile_number__in=[
            mobile_number,  # অরিজিনাল
            clean_mobile,   # শুধু সংখ্যা
        ]
    ).order_by('-created_at')

    if not all_invoices.exists():
        messages.error(request, f'❌ {mobile_number} নাম্বারের কোনো ভাউচার পাওয়া যায়নি। সঠিক মোবাইল নাম্বার দিয়ে চেষ্টা করুন।')
        return redirect('invoice_list')

    # কাস্টমার তথ্য
    customer_name = all_invoices.first().customer_name

    # মোট হিসাব
    total_purchase = sum(inv.total_amount for inv in all_invoices if inv.is_latest)
    total_paid = sum(inv.paid_amount for inv in all_invoices if inv.is_latest)
    total_due = sum(inv.due_amount for inv in all_invoices if inv.is_latest)

    context = {
        'customer_name': customer_name,
        'mobile_number': mobile_number,
        'all_invoices': all_invoices,
        'total_purchase': total_purchase,
        'total_paid': total_paid,
        'total_due': total_due,
    }
    return render(request, 'admin_panel/customer_profile.html', context)


@login_required
def order_customer_profile(request, mobile_number):
    """কাস্টম অর্ডার কাস্টমার প্রোফাইল - একজন কাস্টমারের সব অর্ডার"""
    # মোবাইল নাম্বার থেকে শুধু সংখ্যা বের করা (স্পেস/ড্যাশ অপসারণ)
    clean_mobile = ''.join(filter(str.isdigit, mobile_number))

    # এই মোবাইল নাম্বারের সব অর্ডার
    all_orders = Order.objects.filter(
        mobile_number__in=[
            mobile_number,  # অরিজিনাল
            clean_mobile,   # শুধু সংখ্যা
        ]
    ).order_by('-created_at')

    if not all_orders.exists():
        messages.error(request, f'❌ {mobile_number} নাম্বারের কোনো অর্ডার পাওয়া যায়নি। সঠিক মোবাইল নাম্বার দিয়ে চেষ্টা করুন।')
        return redirect('order_list')

    # কাস্টমার তথ্য
    customer_name = all_orders.first().customer_name

    # মোট হিসাব
    total_orders = all_orders.count()
    total_price = sum(ord.total_price for ord in all_orders)
    total_paid = sum(ord.cash_paid for ord in all_orders)
    total_due = sum(ord.due_amount for ord in all_orders)

    # ডেলিভারি স্ট্যাটাস কাউন্ট
    delivered_count = all_orders.filter(delivery_status='delivered').count()
    pending_count = all_orders.filter(delivery_status='not_delivered').count()

    context = {
        'customer_name': customer_name,
        'mobile_number': mobile_number,
        'all_orders': all_orders,
        'total_orders': total_orders,
        'total_price': total_price,
        'total_paid': total_paid,
        'total_due': total_due,
        'delivered_count': delivered_count,
        'pending_count': pending_count,
    }
    return render(request, 'admin_panel/order_customer_profile.html', context)


# ইউজার ম্যানেজমেন্ট (শুধু সুপার অ্যাডমিনের জন্য)
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings

@login_required
def user_management(request):
    """ইউজার ম্যানেজমেন্ট - শুধু সুপার অ্যাডমিনের জন্য"""
    # চেক করুন ইউজার সুপার অ্যাডমিন কিনা
    if not request.user.is_superuser:
        messages.error(request, '❌ আপনার এই পেজে প্রবেশের অনুমতি নেই!')
        return redirect('admin_dashboard')

    # সব ইউজার (সুপার অ্যাডমিন ছাড়া)
    users = User.objects.filter(is_superuser=False).order_by('-date_joined')

    context = {
        'users': users,
    }
    return render(request, 'admin_panel/user_management.html', context)


@login_required
def user_create(request):
    """নতুন ম্যানেজার তৈরি করুন"""
    if not request.user.is_superuser:
        messages.error(request, '❌ আপনার এই কাজ করার অনুমতি নেই!')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        full_name = request.POST.get('full_name')

        # চেক করুন ইউজারনেম আছে কিনা
        if User.objects.filter(username=username).exists():
            messages.error(request, f'❌ "{username}" ইউজারনেম ইতিমধ্যে ব্যবহৃত হয়েছে!')
            return redirect('user_management')

        # নতুন ইউজার তৈরি
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=full_name,
            is_staff=True,
            is_superuser=False
        )

        # ইমেইল পাঠান
        try:
            send_mail(
                subject='নতুন ম্যানেজার অ্যাকাউন্ট তৈরি হয়েছে - বাধন স্টিল',
                message=f'''
নমস্কার {full_name},

আপনার জন্য বাধন স্টিল অ্যাডমিন প্যানেলে একটি ম্যানেজার অ্যাকাউন্ট তৈরি করা হয়েছে।

লগইন তথ্য:
ইউজারনেম: {username}
পাসওয়ার্ড: {password}

লগইন লিংক: http://127.0.0.1:8001/admin-panel/login/

দয়া করে লগইন করার পর আপনার পাসওয়ার্ড পরিবর্তন করুন।

ধন্যবাদ,
বাধন স্টিল টিম
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            # সুপার অ্যাডমিনকেও ইমেইল পাঠান
            send_mail(
                subject='নতুন ম্যানেজার যোগ করা হয়েছে - বাধন স্টিল',
                message=f'''
নতুন ম্যানেজার যোগ করা হয়েছে:

নাম: {full_name}
ইউজারনেম: {username}
ইমেইল: {email}
তারিখ: {user.date_joined.strftime("%d/%m/%Y %H:%M")}

ধন্যবাদ,
বাধন স্টিল সিস্টেম
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[],
                fail_silently=False,
            )

            messages.success(request, f'✅ ম্যানেজার "{full_name}" সফলভাবে যোগ করা হয়েছে! ইমেইল পাঠানো হয়েছে।')
        except Exception as e:
            messages.warning(request, f'✅ ম্যানেজার যোগ হয়েছে কিন্তু ইমেইল পাঠাতে সমস্যা হয়েছে: {str(e)}')

        return redirect('user_management')

    return redirect('user_management')


@login_required
def user_delete(request, user_id):
    """ম্যানেজার রিমুভ করুন"""
    if not request.user.is_superuser:
        messages.error(request, '❌ আপনার এই কাজ করার অনুমতি নেই!')
        return redirect('admin_dashboard')

    user = get_object_or_404(User, pk=user_id)

    # সুপার অ্যাডমিন ডিলিট করা যাবে না
    if user.is_superuser:
        messages.error(request, '❌ সুপার অ্যাডমিন ডিলিট করা যাবে না!')
        return redirect('user_management')

    username = user.username
    user.delete()
    messages.success(request, f'✅ ম্যানেজার "{username}" সফলভাবে রিমুভ করা হয়েছে!')
    return redirect('user_management')


@login_required
def user_reset_password(request, user_id):
    """ম্যানেজারের পাসওয়ার্ড রিসেট করুন"""
    if not request.user.is_superuser:
        messages.error(request, '❌ আপনার এই কাজ করার অনুমতি নেই!')
        return redirect('admin_dashboard')

    if request.method == 'POST':
        user = get_object_or_404(User, pk=user_id)
        new_password = request.POST.get('new_password')

        user.set_password(new_password)
        user.save()

        # ইমেইল পাঠান
        try:
            send_mail(
                subject='পাসওয়ার্ড রিসেট করা হয়েছে - বাধন স্টিল',
                message=f'''
নমস্কার {user.first_name},

আপনার বাধন স্টিল অ্যাডমিন প্যানেলের পাসওয়ার্ড রিসেট করা হয়েছে।

নতুন লগইন তথ্য:
ইউজারনেম: {user.username}
পাসওয়ার্ড: {new_password}

লগইন লিংক: http://127.0.0.1:8001/admin-panel/login/

ধন্যবাদ,
বাধন স্টিল টিম
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            messages.success(request, f'✅ পাসওয়ার্ড রিসেট করা হয়েছে এবং ইমেইল পাঠানো হয়েছে!')
        except Exception as e:
            messages.warning(request, f'✅ পাসওয়ার্ড রিসেট হয়েছে কিন্তু ইমেইল পাঠাতে সমস্যা হয়েছে: {str(e)}')

        return redirect('user_management')

    return redirect('user_management')


@login_required
def order_payment_create(request, order_pk):
    """কাস্টম অর্ডারের জন্য আংশিক পেমেন্ট যোগ করা"""
    order = get_object_or_404(Order, pk=order_pk)

    if request.method == 'POST':
        form = OrderPaymentForm(request.POST)
        if form.is_valid():
            # Validate not overpaying
            amount = form.cleaned_data.get('amount')
            try:
                amount_value = Decimal(str(amount))
            except Exception:
                messages.error(request, '❌ অনুগ্রহ করে সঠিক পরিমাণ লিখুন।')
                return redirect('order_payment_create', order_pk=order.pk)

            # CORRECT CALCULATION: Total paid = ALL OrderPayment records (cash_paid now reflects total)
            # After signal fix, cash_paid always = sum(OrderPayments)
            current_total_paid = Decimal(str(order.cash_paid))
            total_price = Decimal(str(order.total_price))

            if (current_total_paid + amount_value) > total_price:
                max_allowed = total_price - current_total_paid
                messages.error(request, f'❌ অতিরিক্ত পেমেন্ট! মোট মূল্য: ৳{order.total_price}, ইতিমধ্যে পরিশোধিত: ৳{current_total_paid}। সর্বোচ্চ যুক্ত করতে পারেন: ৳{max_allowed}')
                return redirect('order_payment_create', order_pk=order.pk)

            try:
                payment = form.save(commit=False)
                payment.order = order
                payment.save()
                # Signal will update order.cash_paid and due_amount
                # Refresh order from DB to get updated totals
                order.refresh_from_db()

                messages.success(request, f'✅ পেমেন্ট ৳{payment.amount} সফলভাবে যোগ করা হয়েছে!')
                return redirect('order_customer_profile', mobile_number=order.mobile_number)
            except Exception as e:
                messages.error(request, f'❌ ত্রুটি: {str(e)}')
    else:
        form = OrderPaymentForm()

    context = {
        'form': form,
        'order': order,
    }
    return render(request, 'admin_panel/order_payment_form.html', context)


@login_required
def order_payment_edit(request, pk):
    """Edit an existing OrderPayment for a custom order.

    Uses the same overpayment protection logic and relies on the
    OrderPayment signals to keep Order.cash_paid and Order.due_amount
    in sync.
    """
    payment = get_object_or_404(OrderPayment, pk=pk)
    order = payment.order

    if request.method == 'POST':
        form = OrderPaymentForm(request.POST, instance=payment)
        if form.is_valid():
            updated_payment = form.save(commit=False)
            new_amount = updated_payment.amount

            # Sum of all other payments for this order
            other_total = sum(p.amount for p in order.payments.exclude(pk=payment.pk))
            total_price = order.total_price
            max_allowed = total_price - other_total

            if new_amount > max_allowed:
                messages.error(
                    request,
                    f'❌ অতিরিক্ত পেমেন্ট! মোট মূল্য: ৳{order.total_price}, অন্য পেমেন্টসমূহ: ৳{other_total}। সর্বোচ্চ পরিমাণ: ৳{max_allowed}',
                )
            else:
                payment.amount = updated_payment.amount
                payment.payment_date = updated_payment.payment_date
                payment.notes = updated_payment.notes
                payment.save()

                # Signal will update order.cash_paid and order.due_amount
                order.refresh_from_db()
                messages.success(request, '✅ পেমেন্ট সফলভাবে আপডেট করা হয়েছে!')
                return redirect('order_customer_profile', mobile_number=order.mobile_number)
    else:
        form = OrderPaymentForm(instance=payment)

    # Ensure latest totals are displayed
    order.refresh_from_db()

    context = {
        'form': form,
        'order': order,
        'payment': payment,
    }
    return render(request, 'admin_panel/order_payment_form.html', context)


@login_required
def order_payment_delete(request, pk):
    """Delete an OrderPayment and update the parent order totals."""
    payment = get_object_or_404(OrderPayment, pk=pk)
    order = payment.order

    try:
        payment.delete()
        # Signal will recalculate cash_paid and due_amount
        order.refresh_from_db()
        messages.success(request, '✅ পেমেন্ট সফলভাবে মুছে ফেলা হয়েছে!')
    except Exception as e:
        messages.error(request, f'❌ পেমেন্ট মুছতে ত্রুটি: {str(e)}')

    return redirect('order_customer_profile', mobile_number=order.mobile_number)


@login_required
def admin_statistics(request):
    """অ্যাডমিন স্ট্যাটিস্টিক্স পেজ - শুধুমাত্র সুপার অ্যাডমিনের জন্য"""
    if not request.user.is_superuser:
        messages.error(request, '❌ আপনার এই পেজে অ্যাক্সেস করার অনুমতি নেই!')
        return redirect('admin_dashboard')
    
    try:
        # তারিখ গণনা
        today = timezone.now().date()
        one_month_ago = today - timedelta(days=30)
        
        # পণ্য স্ট্যাটিস্টিক্স
        total_products = InventoryProduct.objects.count()
        active_products = InventoryProduct.objects.filter(is_active=True).count()
        inactive_products = total_products - active_products
        
        # মোট পণ্যের মূল্য (স্টক × ইউনিট প্রাইস)
        products_for_value = InventoryProduct.objects.filter(is_active=True)
        total_inventory_value = Decimal('0')
        for product in products_for_value:
            total_inventory_value += product.stock_quantity * product.price_per_unit
        
        # স্টক স্ট্যাটিস্টিক্স
        products_with_stock = InventoryProduct.objects.filter(
            is_active=True, 
            stock_quantity__gt=0
        ).count()
        out_of_stock_products = active_products - products_with_stock
        
        # শেষ ১ মাসের অর্ডার স্ট্যাটিস্টিক্স
        last_month_orders = Order.objects.filter(created_at__date__gte=one_month_ago)
        total_orders_last_month = last_month_orders.count()
        
        # শেষ ১ মাসের অর্ডারের মোট মূল্য
        total_order_value_last_month = last_month_orders.aggregate(
            total=Sum('total_price')
        )['total'] or Decimal('0')
        
        # শেষ ১ মাসের ইনভয়েস স্ট্যাটিস্টিক্স
        last_month_invoices = Invoice.objects.filter(created_at__date__gte=one_month_ago)
        total_invoices_last_month = last_month_invoices.count()
        
        # শেষ ১ মাসের ইনভয়েসের মোট মূল্য (ডিসকাউন্টের পরে প্রকৃত বিক্রয় মূল্য)
        total_invoice_value_last_month = last_month_invoices.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')
        
        # শেষ ১ মাসের মোট বিক্রয় (অর্ডার + ইনভয়েস)
        total_sales_last_month = total_order_value_last_month + total_invoice_value_last_month
        
        # গড় অর্ডার মূল্য
        avg_order_value = last_month_orders.aggregate(
            avg=Avg('total_price')
        )['avg'] or Decimal('0')
        
        # গড় ইনভয়েস মূল্য
        avg_invoice_value = last_month_invoices.aggregate(
            avg=Avg('subtotal')
        )['avg'] or Decimal('0')
        
    except Exception as e:
        # If anything fails, show error message and redirect to dashboard
        print(f"ERROR in admin_statistics: {e}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'❌ স্ট্যাটিস্টিক্স লোড করতে ত্রুটি: {str(e)}')
        return redirect('admin_dashboard')
    
    # টপ ১০ সবচেয়ে বেশি মূল্যের পণ্য
    all_products = list(InventoryProduct.objects.filter(is_active=True))
    # Calculate value in Python to avoid database expression issues
    for product in all_products:
        product.calculated_value = float(product.stock_quantity) * float(product.price_per_unit)
    all_products.sort(key=lambda p: p.calculated_value, reverse=True)
    top_valuable_products = all_products[:10]
    
    # টপ ১০ সবচেয়ে বেশি স্টকের পণ্য
    top_stock_products = InventoryProduct.objects.filter(
        is_active=True
    ).order_by('-stock_quantity')[:10]
    
    # কম স্টকের পণ্য (১০ টির কম)
    low_stock_products = InventoryProduct.objects.filter(
        is_active=True,
        stock_quantity__lt=10,
        stock_quantity__gt=0
    ).order_by('stock_quantity')[:10]

    # কাস্টমারদের বাকি টাকা (অর্ডার + ইনভয়েস)
    order_dues_qs = Order.objects.filter(due_amount__gt=0)
    invoice_dues_qs = Invoice.objects.filter(due_amount__gt=0, is_latest=True)

    total_order_due = order_dues_qs.aggregate(total=Sum('due_amount'))['total'] or Decimal('0')
    total_invoice_due = invoice_dues_qs.aggregate(total=Sum('due_amount'))['total'] or Decimal('0')
    total_due_all = total_order_due + total_invoice_due

    from collections import defaultdict
    customer_map = defaultdict(lambda: {
        'customer_name': '',
        'mobile_number': '',
        'order_due': Decimal('0'),
        'invoice_due': Decimal('0'),
        'total_due': Decimal('0'),
    })

    for row in order_dues_qs.values('customer_name', 'mobile_number').annotate(total=Sum('due_amount')):
        key = row['mobile_number'] or row['customer_name'] or 'UNKNOWN'
        entry = customer_map[key]
        entry['customer_name'] = row['customer_name'] or entry['customer_name']
        entry['mobile_number'] = row['mobile_number'] or entry['mobile_number']
        entry['order_due'] += row['total'] or Decimal('0')

    for row in invoice_dues_qs.values('customer_name', 'mobile_number').annotate(total=Sum('due_amount')):
        key = row['mobile_number'] or row['customer_name'] or 'UNKNOWN'
        entry = customer_map[key]
        entry['customer_name'] = row['customer_name'] or entry['customer_name']
        entry['mobile_number'] = row['mobile_number'] or entry['mobile_number']
        entry['invoice_due'] += row['total'] or Decimal('0')

    # মোট বাকি হিসাব করে সাজানো লিস্ট (টপ ১০)
    top_due_customers = []
    for entry in customer_map.values():
        entry['total_due'] = entry['order_due'] + entry['invoice_due']
        if entry['total_due'] > 0:
            top_due_customers.append(entry)

    top_due_customers.sort(key=lambda x: x['total_due'], reverse=True)
    top_due_customers = top_due_customers[:10]

    context = {
        'total_products': total_products,
        'active_products': active_products,
        'inactive_products': inactive_products,
        'total_inventory_value': total_inventory_value,
        'products_with_stock': products_with_stock,
        'out_of_stock_products': out_of_stock_products,
        'total_orders_last_month': total_orders_last_month,
        'total_invoices_last_month': total_invoices_last_month,
        'total_order_value_last_month': total_order_value_last_month,
        'total_invoice_value_last_month': total_invoice_value_last_month,
        'total_sales_last_month': total_sales_last_month,
        'avg_order_value': avg_order_value,
        'avg_invoice_value': avg_invoice_value,
        'top_valuable_products': top_valuable_products,
        'top_stock_products': top_stock_products,
        'low_stock_products': low_stock_products,
        'total_order_due': total_order_due,
        'total_invoice_due': total_invoice_due,
        'total_due_all': total_due_all,
        'top_due_customers': top_due_customers,
        'one_month_ago': one_month_ago,
        'today': today,
    }
    
    return render(request, 'admin_panel/admin_statistics.html', context)


# ==================== বাকি খাতা (Due Accounts) ====================

@login_required
def due_accounts_list(request):
    """বাকি খাতা - সব অর্ডার যেগুলোর বাকি আছে (ক্রেতা অনুযায়ী গ্রুপকৃত)"""
    search_query = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)
    
    # Get all orders with due amounts (both from Order and Invoice models)
    orders_with_due = Order.objects.filter(due_amount__gt=0).select_related('customer').order_by('-created_at')
    invoices_with_due = Invoice.objects.filter(due_amount__gt=0, is_latest=True).order_by('-created_at')
    
    # Group by customer to show total due per customer
    customer_due = {}
    
    # Process orders
    for order in orders_with_due:
        # Use final_price if available, otherwise total_price
        total_amount = order.final_price if order.final_price > 0 else order.total_price
        due_amount = order.due_amount if order.due_amount > 0 else (total_amount - order.cash_paid)
        
        if due_amount > 0:  # Only show if there's actually due
            # Use customer object if available, otherwise customer_name
            if order.customer:
                customer_key = f"customer_{order.customer.pk}"
                customer_name = order.customer.name
                mobile_number = order.customer.mobile_number
                customer_obj = order.customer
            else:
                # Fallback to customer_name for orders without customer object
                customer_key = f"name_{order.customer_name}_{order.mobile_number}"
                customer_name = order.customer_name
                mobile_number = order.mobile_number
                customer_obj = None
            
            if customer_key not in customer_due:
                customer_due[customer_key] = {
                    'customer': customer_obj,
                    'customer_name': customer_name,
                    'mobile_number': mobile_number,
                    'total_amount': Decimal('0'),
                    'paid_amount': Decimal('0'),
                    'due_amount': Decimal('0'),
                    'order_count': 0,
                    'last_date': order.created_at,
                }
            
            customer_due[customer_key]['total_amount'] += total_amount
            customer_due[customer_key]['paid_amount'] += order.cash_paid
            customer_due[customer_key]['due_amount'] += due_amount
            customer_due[customer_key]['order_count'] += 1
            
            # Update last date if this order is newer
            if order.created_at > customer_due[customer_key]['last_date']:
                customer_due[customer_key]['last_date'] = order.created_at
    
    # Process invoices
    for invoice in invoices_with_due:
        # Calculate actual paid amount from payments if they exist
        total_paid = sum(p.amount for p in invoice.payments.all()) if invoice.payments.exists() else invoice.paid_amount
        actual_due = invoice.total_amount - total_paid
        
        if actual_due > 0:  # Only show if there's actually due
            customer_key = f"name_{invoice.customer_name}_{invoice.mobile_number}"
            
            if customer_key not in customer_due:
                customer_due[customer_key] = {
                    'customer': None,
                    'customer_name': invoice.customer_name,
                    'mobile_number': invoice.mobile_number,
                    'total_amount': Decimal('0'),
                    'paid_amount': Decimal('0'),
                    'due_amount': Decimal('0'),
                    'order_count': 0,
                    'last_date': invoice.created_at,
                }
            
            customer_due[customer_key]['total_amount'] += invoice.total_amount
            customer_due[customer_key]['paid_amount'] += total_paid
            customer_due[customer_key]['due_amount'] += actual_due
            customer_due[customer_key]['order_count'] += 1
            
            # Update last date if this invoice is newer
            if invoice.created_at > customer_due[customer_key]['last_date']:
                customer_due[customer_key]['last_date'] = invoice.created_at
    
    # Process customers from transactions app with negative balance (বাকি)
    from transactions.models import Customer as TransactionCustomer
    transaction_customers_with_due = TransactionCustomer.objects.filter(
        current_balance__lt=0,
        is_deleted=False
    ).order_by('-updated_at')
    
    for txn_customer in transaction_customers_with_due:
        # Negative balance means customer owes money (বাকি)
        due_amount = abs(txn_customer.current_balance)
        
        customer_key = f"txn_customer_{txn_customer.pk}"
        
        if customer_key not in customer_due:
            # Count completed transactions for this customer
            from transactions.models import Transaction
            transaction_count = Transaction.objects.filter(
                customer=txn_customer,
                is_reversed=False,
                is_deleted=False
            ).exclude(
                transaction_type='purchase',
                status='cancelled'
            ).count()
            
            customer_due[customer_key] = {
                'customer': None,
                'customer_name': txn_customer.name,
                'mobile_number': txn_customer.mobile_number,
                'total_amount': txn_customer.total_purchased,
                'paid_amount': txn_customer.total_submitted,
                'due_amount': due_amount,
                'order_count': transaction_count,
                'last_date': txn_customer.updated_at,
            }
    
    # Convert to list and apply search filter
    due_items = list(customer_due.values())
    
    if search_query:
        due_items = [
            item for item in due_items
            if search_query.lower() in item['customer_name'].lower() 
            or search_query.lower() in item['mobile_number'].lower()
        ]
    
    # Sort by last date (most recent activity first)
    due_items.sort(key=lambda x: x['last_date'], reverse=True)
    
    # Calculate totals
    total_amount = sum(item['total_amount'] for item in due_items)
    total_paid = sum(item['paid_amount'] for item in due_items)
    total_due = sum(item['due_amount'] for item in due_items)
    
    # Pagination
    paginator = Paginator(due_items, 20)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'due_items': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_due': total_due,
    }
    return render(request, 'admin_panel/due_accounts_list.html', context)


@login_required
def due_accounts_print(request):
    """বাকি খাতা প্রিন্ট - প্রিন্টেবল ফরম্যাট"""
    shop_info = ShopInfo.objects.first()
    
    # Get all orders with due amounts (only custom orders for now)
    orders_with_due = Order.objects.filter(due_amount__gt=0).select_related('customer').order_by('-created_at')
    
    # Group by customer to show total due per customer
    customer_due = {}
    total_grand_due = Decimal('0')
    
    for order in orders_with_due:
        if order.customer:
            customer_id = order.customer.pk
            if customer_id not in customer_due:
                customer_due[customer_id] = {
                    'customer': order.customer,
                    'total_due': Decimal('0'),
                    'orders': []
                }
            customer_due[customer_id]['total_due'] += order.due_amount
            customer_due[customer_id]['orders'].append(order)
            total_grand_due += order.due_amount
        else:
            # For orders without customer (old orders)
            key = f"mobile_{order.mobile_number}"
            if key not in customer_due:
                customer_due[key] = {
                    'customer_name': order.customer_name,
                    'mobile_number': order.mobile_number,
                    'total_due': Decimal('0'),
                    'orders': []
                }
            customer_due[key]['total_due'] += order.due_amount
            customer_due[key]['orders'].append(order)
            total_grand_due += order.due_amount
    
    context = {
        'shop_info': shop_info,
        'customer_due': customer_due,
        'total_grand_due': total_grand_due,
        'print_date': timezone.now(),
    }
    return render(request, 'admin_panel/due_accounts_print.html', context)


# ==================== কাস্টমার লিস্ট (Customer List) ====================

@login_required
def customer_list(request):
    """কাস্টমার লিস্ট - সব কাস্টমারের তথ্য"""
    search_query = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)
    
    # Get all customers from Customer model with annotations
    customers = Customer.objects.annotate(
        total_due=Sum('orders__due_amount')
    ).order_by('-created_at')
    
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(mobile_number__icontains=search_query)
        )
    
    paginator = Paginator(customers, 20)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customers': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'admin_panel/customer_list.html', context)


# ==================== PDF Generation Views ====================

@login_required
def print_inventory_pdf(request):
    """ইনভেন্টরি স্টক পিডিএফ প্রিন্ট"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="inventory_stocks.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Unit mapping to English
    unit_map = {
        'piece': 'Piece',
        'feet': 'Feet',
        'meter': 'Meter',
        'ton': 'Ton',
        'kg': 'Kg'
    }
    
    # Get shop info
    shop_info = ShopInfo.objects.first()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    if shop_info:
        elements.append(Paragraph(f"{shop_info.name}", title_style))
        elements.append(Paragraph("Inventory Stock Report", styles['Heading2']))
    else:
        elements.append(Paragraph("Inventory Stock Report", title_style))
    
    elements.append(Spacer(1, 12))
    
    # Get all products
    products = InventoryProduct.objects.all().order_by('name')
    
    # Table data - using English headers for better compatibility
    table_data = [['No.', 'Product Name', 'Unit', 'Price/Unit', 'Stock Qty', 'Total Value']]
    
    total_value = 0
    for idx, product in enumerate(products, 1):
        total_price = product.stock_quantity * product.price_per_unit
        total_value += total_price
        unit_display = unit_map.get(product.unit, product.unit)
        table_data.append([
            str(idx),
            product.name,
            unit_display,
            f"Tk.{product.price_per_unit}",
            f"{product.stock_quantity}",
            f"Tk.{total_price}"
        ])
    
    table_data.append(['', '', '', '', 'Total:', f"Tk.{total_value}"])
    
    # Create table
    table = Table(table_data, colWidths=[0.5*inch, 2.5*inch, 1*inch, 1*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#667eea'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#ffffff'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#f8f9fa'),
        ('GRID', (0, 0), (-1, -1), 1, '#dddddd'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Footer with date
    elements.append(Paragraph(f"Print Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    
    doc.build(elements)
    return response


@login_required
def print_selected_inventory_pdf(request):
    """নির্বাচিত ইনভেন্টরি পণ্যের স্টক পিডিএফ প্রিন্ট"""
    if request.method != 'POST':
        messages.error(request, '❌ পণ্য নির্বাচন করুন!')
        return redirect('inventory_product_list')
    
    selected_product_ids = request.POST.getlist('selected_products')
    
    if not selected_product_ids:
        messages.error(request, '❌ কমপক্ষে একটি পণ্য নির্বাচন করুন!')
        return redirect('inventory_product_list')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="selected_inventory_stocks.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Unit mapping to English
    unit_map = {
        'piece': 'Piece',
        'feet': 'Feet',
        'meter': 'Meter',
        'ton': 'Ton',
        'kg': 'Kg'
    }
    
    # Get shop info
    shop_info = ShopInfo.objects.first()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    if shop_info:
        elements.append(Paragraph(f"{shop_info.name}", title_style))
        elements.append(Paragraph("Selected Inventory Stock Report", styles['Heading2']))
    else:
        elements.append(Paragraph("Selected Inventory Stock Report", title_style))
    
    elements.append(Spacer(1, 12))
    
    # Get selected products
    products = InventoryProduct.objects.filter(pk__in=selected_product_ids).order_by('name')
    
    # Table data - using English headers for better compatibility
    table_data = [['No.', 'Product Name', 'Unit', 'Price/Unit', 'Stock Qty', 'Total Value']]
    
    total_value = 0
    for idx, product in enumerate(products, 1):
        total_price = product.stock_quantity * product.price_per_unit
        total_value += total_price
        unit_display = unit_map.get(product.unit, product.unit)
        table_data.append([
            str(idx),
            product.name,
            unit_display,
            f"Tk.{product.price_per_unit}",
            f"{product.stock_quantity}",
            f"Tk.{total_price}"
        ])
    
    table_data.append(['', '', '', '', 'Total:', f"Tk.{total_value}"])
    
    # Create table
    table = Table(table_data, colWidths=[0.5*inch, 2.5*inch, 1*inch, 1*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#667eea'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#ffffff'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#f8f9fa'),
        ('GRID', (0, 0), (-1, -1), 1, '#dddddd'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Footer with date
    elements.append(Paragraph(f"Print Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    
    doc.build(elements)
    return response


@login_required
def print_stock_history_pdf(request):
    """স্টক হিস্ট্রি পিডিএফ প্রিন্ট"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="stock_history.pdf"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Get shop info
    shop_info = ShopInfo.objects.first()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    if shop_info:
        elements.append(Paragraph(f"{shop_info.name}", title_style))
        elements.append(Paragraph("Stock History Report", styles['Heading2']))
    else:
        elements.append(Paragraph("Stock History Report", title_style))
    
    elements.append(Spacer(1, 12))
    
    # Get stock history
    stock_history = StockHistory.objects.all().order_by('-created_at')[:100]  # Last 100 records
    
    # Table data - using English headers for better compatibility
    table_data = [['Date', 'Product Name', 'Operation', 'Quantity', 'Before', 'After', 'Notes']]
    
    for history in stock_history:
        # Map operation to English for clarity
        operation_map = {
            'add': 'STOCK ADDED',
            'remove': 'STOCK REMOVED',
            'sale': 'SOLD',
            'adjustment': 'ADJUSTED'
        }
        operation_text = operation_map.get(history.operation, history.operation.upper())
        
        table_data.append([
            history.created_at.strftime('%Y-%m-%d %H:%M'),
            history.product.name,
            operation_text,
            f"{history.quantity}",
            f"{history.previous_quantity}",
            f"{history.new_quantity}",
            history.notes[:30] if history.notes else '-'
        ])
    
    # Create table
    table = Table(table_data, colWidths=[1.2*inch, 2*inch, 1*inch, 0.6*inch, 0.6*inch, 0.6*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#667eea'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#ffffff'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#f8f9fa'),
        ('GRID', (0, 0), (-1, -1), 1, '#dddddd'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    # Footer with date
    elements.append(Paragraph(f"Print Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    
    doc.build(elements)
    return response



# ==================== টেস্ট কাস্টম অর্ডার ভিউ (PRODUCTION GRADE) ====================

@login_required
def test_order_create(request):
    """অর্ডার তৈরি - ক্রেতা সিলেক্ট করে পurchase transaction"""
    # Get all test customers for selection
    test_customers = TestCustomer.objects.all().order_by('name')
    
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        
        if not customer_id:
            messages.error(request, '❌ অনুগ্রহ করে একটি ক্রেতা নির্বাচন করুন!')
        else:
            try:
                customer = TestCustomer.objects.get(pk=customer_id)
                # Redirect to purchase creation for this customer
                return redirect('test_transaction_purchase_create', customer_pk=customer.pk)
            except TestCustomer.DoesNotExist:
                messages.error(request, '❌ ক্রেতা পাওয়া যায়নি!')
    
    context = {
        'test_customers': test_customers,
        'page_title': 'নতুন অর্ডার তৈরি করুন',
    }
    return render(request, 'admin_panel/test_order_create.html', context)


@login_required
def import_custom_orders_to_test(request):
    """Import customers and orders from custom order system to test order system"""
    from django.core.management import call_command
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'dry_run':
            # Dry run - show what would be imported
            from io import StringIO
            import sys
            
            output = StringIO()
            sys.stdout = output
            
            try:
                call_command('import_custom_orders_to_test', dry_run=True)
                result = output.getvalue()
                messages.success(request, '✅ Dry run completed. Check the output below.')
            except Exception as e:
                messages.error(request, f'❌ Error during dry run: {str(e)}')
                result = str(e)
            finally:
                sys.stdout = sys.__stdout__
            
            context = {
                'page_title': 'Import Custom Orders to Test System',
                'result': result,
                'is_dry_run': True,
            }
            return render(request, 'admin_panel/import_custom_orders.html', context)
        
        elif action == 'import':
            # Actual import
            try:
                call_command('import_custom_orders_to_test')
                messages.success(request, '✅ Import completed successfully!')
                return redirect('test_customer_list')
            except Exception as e:
                messages.error(request, f'❌ Error during import: {str(e)}')
    
    # GET request - show import page
    # Get statistics
    total_customers = Customer.objects.count()
    total_orders = Order.objects.count()
    test_customers = TestCustomer.objects.count()
    
    # Count customers that would be imported (not already in test system)
    customers_to_import = 0
    for customer in Customer.objects.all():
        if not TestCustomer.objects.filter(mobile_number=customer.mobile_number).exists():
            customers_to_import += 1
    
    context = {
        'page_title': 'Import Custom Orders to Test System',
        'total_customers': total_customers,
        'total_orders': total_orders,
        'test_customers': test_customers,
        'customers_to_import': customers_to_import,
    }
    return render(request, 'admin_panel/import_custom_orders.html', context)


@login_required
def test_customer_list(request):
    """টেস্ট কাস্টমার তালিকা"""
    search_query = request.GET.get('search', '')
    
    customers = TestCustomer.objects.all().order_by('-created_at')
    
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) | Q(mobile_number__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(customers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'customers': page_obj.object_list,
        'search_query': search_query,
        'total_customers': customers.count(),
    }
    return render(request, 'admin_panel/test_customer_list.html', context)


@login_required
def test_customer_create(request):
    """ক্রেতা তৈরি করা"""
    if request.method == 'POST':
        form = TestCustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'✅ {customer.name} সফলভাবে যুক্ত হয়েছে!')
            return redirect('test_customer_detail', pk=customer.pk)
    else:
        form = TestCustomerForm()
    
    context = {
        'form': form,
        'page_title': 'নতুন ক্রেতা তৈরি করুন',
    }
    return render(request, 'admin_panel/test_customer_form.html', context)


@login_required
def test_customer_detail(request, pk):
    """ক্রেতার বিস্তারিত - লেনদেন ভিত্তিক"""
    customer = get_object_or_404(TestCustomer, pk=pk)
    
    # Get all transactions
    transactions = customer.test_transactions.filter(status='completed').order_by('-created_at')
    
    # Get transaction counts
    submission_count = transactions.filter(transaction_type='submission').count()
    purchase_count = transactions.filter(transaction_type='purchase').count()
    withdrawal_count = transactions.filter(transaction_type='withdrawal').count()
    
    context = {
        'customer': customer,
        'transactions': transactions[:10],  # Show last 10
        'total_transactions': transactions.count(),
        'submission_count': submission_count,
        'purchase_count': purchase_count,
        'withdrawal_count': withdrawal_count,
    }
    return render(request, 'admin_panel/test_customer_detail.html', context)


@login_required
def test_customer_edit(request, pk):
    """ক্রেতা সম্পাদনা"""
    customer = get_object_or_404(TestCustomer, pk=pk)
    
    if request.method == 'POST':
        form = TestCustomerForm(request.POST, instance=customer)
        if form.is_valid():
            old_name = customer.name
            old_mobile = customer.mobile_number
            old_address = customer.address
            
            customer = form.save()
            
            # Record history
            TestTransactionHistory.objects.create(
                transaction=None,  # Customer edit, not transaction
                action='edited',
                old_balance=customer.current_balance,
                new_balance=customer.current_balance,
                notes=f'ক্রেতা সম্পাদনা: নাম {old_name} → {customer.name}, মোবাইল {old_mobile} → {customer.mobile_number}',
                performed_by=request.user
            )
            
            messages.success(request, f'✅ {customer.name} সফলভাবে আপডেট হয়েছে!')
            return redirect('test_customer_detail', pk=customer.pk)
    else:
        form = TestCustomerForm(instance=customer)
    
    context = {
        'form': form,
        'customer': customer,
        'page_title': f'{customer.name} - সম্পাদনা করুন',
    }
    return render(request, 'admin_panel/test_customer_form.html', context)


@login_required
def test_customer_delete(request, pk):
    """ক্রেতা মুছে ফেলা - সব লেনদেন সহ"""
    customer = get_object_or_404(TestCustomer, pk=pk)
    
    # Check if customer has transactions
    has_transactions = customer.test_transactions.exists()
    transaction_count = customer.test_transactions.count() if has_transactions else 0
    
    # For POST requests (from form submission) - delete everything
    if request.method == 'POST':
        name = customer.name
        # Delete all transactions first (cascade will handle this, but being explicit)
        if has_transactions:
            customer.test_transactions.all().delete()
        customer.delete()
        
        if has_transactions:
            messages.warning(request, f'⚠️ {name} এবং {transaction_count}টি লেনদেন সফলভাবে মুছে ফেলা হয়েছে!')
        else:
            messages.success(request, f'✅ {name} সফলভাবে মুছে ফেলা হয়েছে!')
        
        return redirect('test_customer_list')
    
    # Show confirmation page for GET requests
    context = {
        'customer': customer,
        'has_transactions': has_transactions,
        'transaction_count': transaction_count,
    }
    return render(request, 'admin_panel/test_customer_delete.html', context)


@login_required
def test_customer_bulk_delete(request):
    """বাল্কভাবে ক্রেতা মুছে ফেলা"""
    if request.method != 'POST':
        messages.error(request, '❌ অবৈধ অনুরোধ')
        return redirect('test_customer_list')
    
    selected_ids = request.POST.getlist('selected_customers')
    
    if not selected_ids:
        messages.error(request, '❌ কোনো কাস্টমার নির্বাচন করা হয়নি')
        return redirect('test_customer_list')
    
    deleted_count = 0
    failed_count = 0
    
    for customer_id in selected_ids:
        try:
            customer = TestCustomer.objects.get(pk=customer_id)
            
            # Check if customer has transactions
            if customer.test_transactions.exists():
                failed_count += 1
                continue
            
            name = customer.name
            customer.delete()
            deleted_count += 1
        except TestCustomer.DoesNotExist:
            failed_count += 1
            continue
    
    if deleted_count > 0:
        messages.success(request, f'✅ {deleted_count}টি কাস্টমার সফলভাবে মুছে ফেলা হয়েছে!')
    
    if failed_count > 0:
        messages.warning(request, f'⚠️ {failed_count}টি কাস্টমার মুছে ফেলা যায়নি (লেনদেন থাকতে পারে)')
    
    return redirect('test_customer_list')


# ==================== টেস্ট লেনদেন - জমা (SUBMISSION) ====================

@login_required
def test_transaction_submission_create(request, customer_pk):
    """লেনদেন - জমা তৈরি করা"""
    customer = get_object_or_404(TestCustomer, pk=customer_pk)
    
    if request.method == 'POST':
        form = TestTransactionSubmissionForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            notes = form.cleaned_data.get('notes', '')
            
            # Create transaction
            transaction = TestCustomerTransaction.objects.create(
                customer=customer,
                transaction_type='submission',
                amount=amount,
                notes=notes,
                status='completed',
                created_by=request.user
            )
            
            # Record history
            TestTransactionHistory.objects.create(
                transaction=transaction,
                action='created',
                old_balance=transaction.balance_before,
                new_balance=transaction.balance_after,
                notes=f'জমা তৈরি: ৳{amount}',
                performed_by=request.user
            )
            
            messages.success(request, f'✅ ৳{amount} জমা সফলভাবে যুক্ত হয়েছে! লেনদেন নং: {transaction.transaction_number}')
            return redirect('test_transaction_voucher', pk=transaction.pk)
    else:
        form = TestTransactionSubmissionForm()
    
    context = {
        'form': form,
        'customer': customer,
        'page_title': f'{customer.name} - নতুন জমা',
    }
    return render(request, 'admin_panel/test_transaction_submission_form.html', context)


# ==================== টেস্ট লেনদেন - ক্রয় (PURCHASE) ====================

@login_required
def test_transaction_purchase_create(request, customer_pk):
    """লেনদেন - ক্রয় তৈরি করা (একাধিক পণ্য + ডিসকাউন্ট সাপোর্ট)"""
    customer = get_object_or_404(TestCustomer, pk=customer_pk)
    
    # Get all inventory products for search
    inventory_products = InventoryProduct.objects.filter(is_active=True, stock_quantity__gt=0).order_by('name')
    products_json = json.dumps([
        {
            'id': p.pk,
            'name': p.name,
            'price': float(p.price_per_unit),
            'unit': p.get_unit_display(),
            'stock': float(p.stock_quantity),
        }
        for p in inventory_products
    ])
    
    # Default dates
    from datetime import timedelta
    today = timezone.now().date()
    default_delivery_date = today + timedelta(days=7)
    
    if request.method == 'POST':
        items_json_str = request.POST.get('items_json', '[]')
        total_discount = request.POST.get('total_discount', '0')
        order_date = request.POST.get('order_date', '')
        delivery_date = request.POST.get('delivery_date', '')
        
        try:
            items_data = json.loads(items_json_str)
        except (json.JSONDecodeError, ValueError):
            items_data = []
        
        # Convert total discount
        try:
            total_discount = Decimal(str(total_discount))
            if total_discount < 0:
                total_discount = Decimal('0')
            if total_discount > 100:
                total_discount = Decimal('100')
        except:
            total_discount = Decimal('0')
        
        # Parse dates
        from datetime import datetime
        order_date_obj = None
        delivery_date_obj = None
        
        if order_date:
            try:
                order_date_obj = datetime.strptime(order_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        if delivery_date:
            try:
                delivery_date_obj = datetime.strptime(delivery_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        if not items_data:
            messages.error(request, '❌ কমপক্ষে একটি পণ্য যোগ করুন!')
        else:
            try:
                validated_items = []
                subtotal = Decimal('0')
                
                # Validate and calculate items
                for item in items_data:
                    product_name = item.get('product_name', '').strip()
                    quantity = Decimal(str(item.get('quantity', 0)))
                    unit_price = Decimal(str(item.get('unit_price', 0)))
                    item_discount = Decimal(str(item.get('discount_percentage', 0)))
                    
                    if not product_name:
                        raise ValueError("পণ্যের নাম লিখুন")
                    if quantity <= 0:
                        raise ValueError(f"{product_name}: পরিমাণ ০-এর বেশি হতে হবে")
                    if unit_price <= 0:
                        raise ValueError(f"{product_name}: মূল্য ০-এর বেশি হতে হবে")
                    if item_discount < 0 or item_discount > 100:
                        raise ValueError(f"{product_name}: ডিসকাউন্ট ০-১০০%-এর মধ্যে হতে হবে")
                    
                    # Find inventory product (stock check will happen AFTER restoring old stock)
                    inventory_product = InventoryProduct.objects.filter(name__iexact=product_name).first()
                    
                    # Calculate item total with discount
                    item_gross = quantity * unit_price
                    item_discount_amount = (item_gross * item_discount) / 100
                    item_net = item_gross - item_discount_amount
                    
                    subtotal += item_net
                    
                    validated_items.append({
                        'product_name': product_name,
                        'product_description': item.get('product_description', ''),
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'discount_percentage': item_discount,
                        'gross_amount': item_gross,
                        'discount_amount': item_discount_amount,
                        'net_amount': item_net,
                        'inventory_product': inventory_product,
                    })
                
                # Apply total discount on subtotal
                total_discount_amount = (subtotal * total_discount) / 100
                final_total = subtotal - total_discount_amount
                
                # Create main transaction
                item_names = ', '.join([item['product_name'] for item in validated_items])
                transaction = TestCustomerTransaction.objects.create(
                    customer=customer,
                    transaction_type='purchase',
                    amount=final_total,
                    item_name=item_names,
                    item_description=f'{len(validated_items)} items purchased',
                    item_quantity=sum(item['quantity'] for item in validated_items),
                    item_unit_price=final_total / sum(item['quantity'] for item in validated_items) if sum(item['quantity'] for item in validated_items) > 0 else Decimal('0'),
                    gross_amount=subtotal + total_discount_amount,
                    item_discount_percentage=total_discount,
                    item_discount_amount=total_discount_amount,
                    total_discount_percentage=total_discount,
                    total_discount_amount=total_discount_amount,
                    notes=request.POST.get('notes', ''),
                    status='completed',
                    created_by=request.user,
                    order_date=order_date_obj,
                    delivery_date=delivery_date_obj
                )
                
                # Create transaction items for each product
                for item in validated_items:
                    TestCustomerTransactionItem.objects.create(
                        transaction=transaction,
                        product_name=item['product_name'],
                        product_description=item['product_description'],
                        quantity=item['quantity'],
                        unit_price=item['unit_price'],
                        discount_percentage=item['discount_percentage'],
                        discount_amount=item['discount_amount'],
                        gross_amount=item['gross_amount'],
                        net_amount=item['net_amount'],
                        inventory_product=item['inventory_product']
                    )
                
                # Deduct stock and create history for inventory products
                for item in validated_items:
                    if item['inventory_product']:
                        inv_product = item['inventory_product']
                        previous_stock = inv_product.stock_quantity
                        inv_product.remove_stock(item['quantity'])
                        
                        StockHistory.objects.create(
                            product=inv_product,
                            operation='sale',
                            quantity=item['quantity'],
                            previous_quantity=previous_stock,
                            new_quantity=inv_product.stock_quantity,
                            notes=f'টেস্ট অর্ডার - {customer.name} ({transaction.transaction_number})'
                        )
                
                messages.success(request, f'✅ ক্রয় সফল! ৳{final_total} | লেনদেন নং: {transaction.transaction_number}')
                return redirect('test_transaction_voucher', pk=transaction.pk)
                
            except ValueError as e:
                messages.error(request, f'❌ {str(e)}')
            except Exception as e:
                messages.error(request, f'❌ ত্রুটি: {str(e)}')
    
    context = {
        'form': None,  # No form needed, using custom template
        'customer': customer,
        'page_title': f'{customer.name} - নতুন ক্রয়',
        'products_json': products_json,
        'today': today,
        'delivery_date': default_delivery_date,
    }
    return render(request, 'admin_panel/test_transaction_purchase_form.html', context)


# ==================== টেস্ট লেনদেন - উত্তোলন (WITHDRAWAL) ====================

@login_required
def test_transaction_withdrawal_create(request, customer_pk):
    """লেনদেন - উত্তোলন তৈরি করা"""
    customer = get_object_or_404(TestCustomer, pk=customer_pk)
    
    if request.method == 'POST':
        form = TestTransactionWithdrawalForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            notes = form.cleaned_data.get('notes', '')
            
            # Create transaction (amount is negative for withdrawal)
            transaction = TestCustomerTransaction.objects.create(
                customer=customer,
                transaction_type='withdrawal',
                amount=amount,
                notes=notes,
                status='completed',
                created_by=request.user
            )
            
            # Record history
            TestTransactionHistory.objects.create(
                transaction=transaction,
                action='created',
                old_balance=transaction.balance_before,
                new_balance=transaction.balance_after,
                notes=f'উত্তোলন তৈরি: ৳{amount}',
                performed_by=request.user
            )
            
            messages.success(request, f'✅ ৳{amount} উত্তোলন সফল! লেনদেন নং: {transaction.transaction_number}')
            return redirect('test_transaction_voucher', pk=transaction.pk)
    else:
        form = TestTransactionWithdrawalForm()
    
    context = {
        'form': form,
        'customer': customer,
        'page_title': f'{customer.name} - টাকা উত্তোলন',
    }
    return render(request, 'admin_panel/test_transaction_withdrawal_form.html', context)


# ==================== টেস্ট লেনদেন - ভাউচার & তালিকা ====================

@login_required
def test_transaction_voucher(request, pk):
    """লেনদেন ভাউচার"""
    transaction = get_object_or_404(TestCustomerTransaction, pk=pk)
    shop_info = ShopInfo.objects.first()
    
    context = {
        'transaction': transaction,
        'customer': transaction.customer,
        'shop_info': shop_info,
    }
    return render(request, 'admin_panel/test_transaction_voucher.html', context)


@login_required
def test_transaction_list(request, customer_pk):
    """লেনদেন তালিকা - নির্দিষ্ট ক্রেতার জন্য"""
    customer = get_object_or_404(TestCustomer, pk=customer_pk)
    
    transaction_type = request.GET.get('type', '')
    date_from = request.GET.get('from_date', '')
    date_to = request.GET.get('to_date', '')
    
    transactions = customer.test_transactions.filter(status='completed').order_by('-created_at')
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if date_from:
        transactions = transactions.filter(created_at__gte=date_from)
    
    if date_to:
        transactions = transactions.filter(created_at__lte=date_to)
    
    # Pagination
    paginator = Paginator(transactions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customer': customer,
        'page_obj': page_obj,
        'transactions': page_obj.object_list,
        'transaction_type': transaction_type,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'admin_panel/test_transaction_list.html', context)


@login_required
def test_transaction_reverse(request, pk):
    """লেনদেন বাতিল/রিভার্স করা"""
    transaction = get_object_or_404(TestCustomerTransaction, pk=pk)
    
    if transaction.is_reversed:
        messages.error(request, '❌ এই লেনদেন ইতিমধ্যেই বাতিল করা হয়েছে!')
        return redirect('test_customer_detail', pk=transaction.customer.pk)
    
    if request.method == 'POST':
        # Store old balance for history
        old_balance = transaction.customer.current_balance
        
        # Create reversal transaction
        reversal_amount = -transaction.amount if transaction.transaction_type == 'submission' else transaction.amount
        
        reversal = TestCustomerTransaction.objects.create(
            customer=transaction.customer,
            transaction_type='reversal',
            amount=reversal_amount,
            notes=f'বাতিল: {transaction.transaction_number} - {transaction.get_transaction_type_display()}',
            reverses_transaction=transaction,
            status='completed',
            created_by=request.user
        )
        
        # Mark original as reversed
        transaction.is_reversed = True
        transaction.save()
        
        # If it was a purchase, restore inventory stock for all items
        if transaction.transaction_type == 'purchase':
            for item in transaction.items.all():
                if item.inventory_product:
                    item.inventory_product.add_stock(item.quantity)
                    
                    # Create stock history
                    StockHistory.objects.create(
                        product=item.inventory_product,
                        operation='adjustment',
                        quantity=item.quantity,
                        previous_quantity=item.inventory_product.stock_quantity - item.quantity,
                        new_quantity=item.inventory_product.stock_quantity,
                        notes=f'লেনদেন বাতিল: {transaction.transaction_number}'
                    )
        
        # Record history for both original and reversal
        TestTransactionHistory.objects.create(
            transaction=transaction,
            action='reversed',
            old_balance=old_balance,
            new_balance=transaction.customer.current_balance,
            notes=f'লেনদেন বাতিল: {transaction.transaction_number}',
            performed_by=request.user
        )
        
        TestTransactionHistory.objects.create(
            transaction=reversal,
            action='created',
            old_balance=old_balance,
            new_balance=reversal.balance_after,
            notes=f'রিভার্সাল তৈরি: {transaction.transaction_number}',
            performed_by=request.user
        )
        
        messages.success(request, f'✅ লেনদেন বাতিল সফল! রিভার্সাল নং: {reversal.transaction_number}')
        return redirect('test_customer_detail', pk=transaction.customer.pk)
    
    context = {
        'transaction': transaction,
        'customer': transaction.customer,
    }
    return render(request, 'admin_panel/test_transaction_reverse_confirm.html', context)


@login_required
def test_customer_statement(request, customer_pk):
    """ক্রেতার স্টেটমেন্ট - সম্পূর্ণ লেনদেন ইতিহাস"""
    customer = get_object_or_404(TestCustomer, pk=customer_pk)
    shop_info = ShopInfo.objects.first()
    
    date_from = request.GET.get('from_date', '')
    date_to = request.GET.get('to_date', '')
    
    transactions = customer.test_transactions.filter(status='completed').order_by('created_at')
    
    if date_from:
        transactions = transactions.filter(created_at__gte=date_from)
    
    if date_to:
        transactions = transactions.filter(created_at__lte=date_to)
    
    context = {
        'customer': customer,
        'shop_info': shop_info,
        'transactions': transactions,
        'date_from': date_from,
        'date_to': date_to,
        'today': timezone.now(),
    }
    return render(request, 'admin_panel/test_customer_statement.html', context)


@login_required
def customer_search_api(request):
    """API endpoint for customer autocomplete search"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'customers': []})
    
    # Search in both Customer and TestCustomer models
    customers = Customer.objects.filter(
        Q(name__icontains=query) | Q(mobile_number__icontains=query)
    )[:10]
    
    test_customers = TestCustomer.objects.filter(
        Q(name__icontains=query) | Q(mobile_number__icontains=query)
    )[:10]
    
    results = []
    
    # Add regular customers
    for customer in customers:
        results.append({
            'id': customer.pk,
            'name': customer.name,
            'mobile': customer.mobile_number,
            'type': 'customer',
            'balance': float(customer.deposit_balance) if hasattr(customer, 'deposit_balance') else 0
        })
    
    # Add test customers
    for customer in test_customers:
        results.append({
            'id': customer.pk,
            'name': customer.name,
            'mobile': customer.mobile_number,
            'type': 'test_customer',
            'balance': float(customer.current_balance)
        })
    
    return JsonResponse({'customers': results})


@login_required
def test_customer_history(request, customer_pk):
    """ক্রেতারের সম্পূর্ণ ইতিহাস - সব অ্যাকশন"""
    customer = get_object_or_404(TestCustomer, pk=customer_pk)
    
    # Get all history records for this customer's transactions
    history_records = TestTransactionHistory.objects.filter(
        transaction__customer=customer
    ).select_related('transaction', 'performed_by').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(history_records, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customer': customer,
        'page_obj': page_obj,
        'history_records': page_obj.object_list,
        'total_records': history_records.count(),
    }
    return render(request, 'admin_panel/test_customer_history.html', context)


@login_required
def test_transaction_edit(request, pk):
    """লেনদেন সম্পাদনা - ক্রয় এডিট"""
    transaction = get_object_or_404(TestCustomerTransaction, pk=pk)
    
    # Only allow editing purchase transactions
    if transaction.transaction_type != 'purchase':
        messages.error(request, '❌ শুধুমাত্র ক্রয় লেনদেন সম্পাদনা করা যাবে!')
        return redirect('test_customer_detail', pk=transaction.customer.pk)
    
    # Don't allow editing reversed transactions
    if transaction.is_reversed:
        messages.error(request, '❌ বাতিল করা লেনদেন সম্পাদনা করা যাবে না!')
        return redirect('test_customer_detail', pk=transaction.customer.pk)
    
    customer = transaction.customer
    
    # Get all inventory products for search
    inventory_products = InventoryProduct.objects.filter(is_active=True, stock_quantity__gt=0).order_by('name')
    products_json = json.dumps([
        {
            'id': p.pk,
            'name': p.name,
            'price': float(p.price_per_unit),
            'unit': p.get_unit_display(),
            'stock': float(p.stock_quantity),
        }
        for p in inventory_products
    ])
    
    if request.method == 'POST':
        items_json_str = request.POST.get('items_json', '[]')
        total_discount = request.POST.get('total_discount', '0')
        
        try:
            items_data = json.loads(items_json_str)
        except (json.JSONDecodeError, ValueError):
            items_data = []
        
        # Convert total discount
        try:
            total_discount = Decimal(str(total_discount))
            if total_discount < 0:
                total_discount = Decimal('0')
            if total_discount > 100:
                total_discount = Decimal('100')
        except:
            total_discount = Decimal('0')
        
        if not items_data:
            messages.error(request, '❌ কমপক্ষে একটি পণ্য যোগ করুন!')
        else:
            try:
                validated_items = []
                subtotal = Decimal('0')
                
                # Validate and calculate items
                for item in items_data:
                    product_name = item.get('product_name', '').strip()
                    quantity = Decimal(str(item.get('quantity', 0)))
                    unit_price = Decimal(str(item.get('unit_price', 0)))
                    item_discount = Decimal(str(item.get('discount_percentage', 0)))
                    
                    if not product_name:
                        raise ValueError("পণ্যের নাম লিখুন")
                    if quantity <= 0:
                        raise ValueError(f"{product_name}: পরিমাণ ০-এর বেশি হতে হবে")
                    if unit_price <= 0:
                        raise ValueError(f"{product_name}: মূল্য ০-এর বেশি হতে হবে")
                    if item_discount < 0 or item_discount > 100:
                        raise ValueError(f"{product_name}: ডিসকাউন্ট ০-১০০%-এর মধ্যে হতে হবে")
                    
                    # Find inventory product but DON'T check stock yet (we'll check after restoring old stock)
                    inventory_product = InventoryProduct.objects.filter(name__iexact=product_name).first()
                    
                    # Calculate item total with discount
                    item_gross = quantity * unit_price
                    item_discount_amount = (item_gross * item_discount) / 100
                    item_net = item_gross - item_discount_amount
                    
                    subtotal += item_net
                    
                    validated_items.append({
                        'product_name': product_name,
                        'product_description': item.get('product_description', ''),
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'discount_percentage': item_discount,
                        'gross_amount': item_gross,
                        'discount_amount': item_discount_amount,
                        'net_amount': item_net,
                        'inventory_product': inventory_product,
                    })
                
                # Apply total discount on subtotal
                total_discount_amount = (subtotal * total_discount) / 100
                final_total = subtotal - total_discount_amount
                
                # Build a map of old items by product name for comparison
                old_items_map = {}
                for old_item in transaction.items.all():
                    if old_item.inventory_product:
                        old_items_map[old_item.inventory_product.pk] = {
                            'item': old_item,
                            'quantity': old_item.quantity
                        }
                    else:
                        old_items_map[old_item.product_name] = {
                            'item': old_item,
                            'quantity': old_item.quantity
                        }
                
                # Update main transaction
                item_names = ', '.join([item['product_name'] for item in validated_items])
                transaction.item_name = item_names
                transaction.item_description = f'{len(validated_items)} items purchased'
                transaction.item_quantity = sum(item['quantity'] for item in validated_items)
                transaction.item_unit_price = final_total / sum(item['quantity'] for item in validated_items) if sum(item['quantity'] for item in validated_items) > 0 else Decimal('0')
                transaction.gross_amount = subtotal + total_discount_amount
                transaction.item_discount_percentage = total_discount
                transaction.item_discount_amount = total_discount_amount
                transaction.total_discount_percentage = total_discount
                transaction.total_discount_amount = total_discount_amount
                transaction.amount = final_total
                transaction.notes = request.POST.get('notes', transaction.notes)
                transaction.save()
                
                # FIRST: Restore old stock for all old items
                restored_items = []
                for old_item in transaction.items.all():
                    # Try to find inventory product by FK first, then by name (case-insensitive)
                    inv_product = old_item.inventory_product
                    if not inv_product:
                        # Try exact match first, then case-insensitive
                        inv_product = InventoryProduct.objects.filter(name__iexact=old_item.product_name).first()
                        if not inv_product:
                            # Try partial match as fallback
                            inv_product = InventoryProduct.objects.filter(name__icontains=old_item.product_name).first()
                    
                    if inv_product:
                        try:
                            # Store old stock level for verification
                            stock_before = float(inv_product.stock_quantity)
                            inv_product.add_stock(old_item.quantity)
                            stock_after = float(inv_product.stock_quantity)
                            restored_items.append(f"{old_item.product_name} (ID:{inv_product.pk}): {stock_before} → {stock_after}")
                        except Exception as e:
                            # If restore fails, log it but continue
                            print(f"WARNING: Failed to restore stock for {old_item.product_name}: {e}")
                    else:
                        print(f"WARNING: No inventory product found for '{old_item.product_name}'")
                
                if restored_items:
                    print(f"✓ Stock restored: {', '.join(restored_items)}")
                else:
                    print("WARNING: No stock was restored!")
                
                # Delete old items and create new ones
                transaction.items.all().delete()
                for item in validated_items:
                    TestCustomerTransactionItem.objects.create(
                        transaction=transaction,
                        product_name=item['product_name'],
                        product_description=item['product_description'],
                        quantity=item['quantity'],
                        unit_price=item['unit_price'],
                        discount_percentage=item['discount_percentage'],
                        discount_amount=item['discount_amount'],
                        gross_amount=item['gross_amount'],
                        net_amount=item['net_amount'],
                        inventory_product=item['inventory_product']
                    )
                
                # THEN: Deduct new stock for all items (now inventory is back to original state)
                for item in validated_items:
                    # Try to find inventory product by FK first, then by name
                    inv_product = item['inventory_product']
                    if not inv_product:
                        inv_product = InventoryProduct.objects.filter(name__iexact=item['product_name']).first()
                    
                    if inv_product:
                        # Check if enough stock available
                        if inv_product.stock_quantity < item['quantity']:
                            raise ValueError(f"{item['product_name']}: স্টক অপর্যাপ্ত! বর্তমান স্টক: {inv_product.stock_quantity} {inv_product.get_unit_display()}, প্রয়োজন: {item['quantity']}")
                        
                        # Deduct stock
                        previous_stock = inv_product.stock_quantity
                        inv_product.remove_stock(item['quantity'])
                        StockHistory.objects.create(
                            product=inv_product,
                            operation='sale',
                            quantity=item['quantity'],
                            previous_quantity=previous_stock,
                            new_quantity=inv_product.stock_quantity,
                            notes=f'টেস্ট অর্ডার এডিট - {customer.name} ({transaction.transaction_number})'
                        )
                
                # Record history
                TestTransactionHistory.objects.create(
                    transaction=transaction,
                    action='edited',
                    old_balance=transaction.balance_before,
                    new_balance=transaction.balance_after,
                    notes=f'ক্রয় সম্পাদনা: {item_names}',
                    performed_by=request.user
                )
                
                messages.success(request, f'✅ ক্রয় সফলভাবে আপডেট হয়েছে! ৳{final_total} | লেনদেন নং: {transaction.transaction_number}')
                return redirect('test_transaction_voucher', pk=transaction.pk)
                
            except ValueError as e:
                messages.error(request, f'❌ {str(e)}')
            except Exception as e:
                messages.error(request, f'❌ ত্রুটি: {str(e)}')
    
    # Build existing items for template
    existing_items = []
    for item in transaction.items.all():
        existing_items.append({
            'product_name': item.product_name,
            'product_description': item.product_description or '',
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'discount_percentage': float(item.discount_percentage),
            'gross_amount': float(item.gross_amount),
            'discount_amount': float(item.discount_amount),
            'net_amount': float(item.net_amount),
            'inventory_product_id': item.inventory_product.pk if item.inventory_product else None,
        })
    
    context = {
        'form': None,
        'customer': customer,
        'transaction': transaction,
        'page_title': f'{customer.name} - ক্রয় সম্পাদনা',
        'products_json': products_json,
        'edit_items_json': json.dumps(existing_items),
        'total_discount': float(transaction.total_discount_percentage),
    }
    return render(request, 'admin_panel/test_transaction_purchase_form.html', context)


# ==================== OLD VIEWS - Keep for backward compatibility ====================


# ==================== OLD VIEWS - Keep for backward compatibility ====================

@login_required
def test_submission_create(request, customer_pk):
    """DEPRECATED - Use test_transaction_submission_create instead"""
    return redirect('test_transaction_submission_create', customer_pk=customer_pk)


@login_required
def test_submission_detail(request, pk):
    """DEPRECATED - টেস্ট জমা বিস্তারিত"""
    submission = get_object_or_404(TestCustomerSubmission, pk=pk)
    items = submission.items.all()
    
    total_spent = sum(item.total_price for item in items)
    remaining = submission.submitted_amount - total_spent
    
    context = {
        'submission': submission,
        'items': items,
        'total_spent': total_spent,
        'remaining': remaining,
    }
    return render(request, 'admin_panel/test_submission_detail.html', context)


@login_required
def test_submission_add_item(request, submission_pk):
    """DEPRECATED - টেস্ট জমায় পণ্য যোগ করা"""
    submission = get_object_or_404(TestCustomerSubmission, pk=submission_pk)
    
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        product_description = request.POST.get('product_description', '')
        quantity = request.POST.get('quantity')
        unit_price = request.POST.get('unit_price')
        
        if product_name and quantity and unit_price:
            try:
                from decimal import Decimal
                quantity = Decimal(quantity)
                unit_price = Decimal(unit_price)
                
                item = TestCustomerItem.objects.create(
                    submission=submission,
                    product_name=product_name,
                    product_description=product_description,
                    quantity=quantity,
                    unit_price=unit_price,
                )
                
                messages.success(request, f'✅ {product_name} সফলভাবে যুক্ত হয়েছে!')
                return redirect('test_submission_detail', pk=submission_pk)
            except Exception as e:
                messages.error(request, f'❌ ত্রুটি: {str(e)}')
    
    context = {
        'submission': submission,
    }
    return render(request, 'admin_panel/test_submission_add_item.html', context)


@login_required
def test_submission_remove_item(request, item_pk):
    """DEPRECATED - টেস্ট জমা থেকে পণ্য সরানো"""
    item = get_object_or_404(TestCustomerItem, pk=item_pk)
    submission = item.submission
    
    if request.method == 'POST':
        product_name = item.product_name
        item.delete()
        messages.success(request, f'✅ {product_name} সফলভাবে সরানো হয়েছে!')
    
    return redirect('test_submission_detail', pk=submission.pk)


# ==================== REDIRECT VIEWS FOR OLD URLS ====================
@login_required
def redirect_order_list(request, **kwargs):
    """Redirect old order list URL to transactions app"""
    return redirect('transactions:customer_list')


@login_required
def redirect_order_create(request):
    """Redirect old order create URL to transactions app"""
    return redirect('transactions:order_create')


@login_required
def redirect_order_voucher(request, pk):
    """Redirect old order voucher URL to transactions app"""
    return redirect('transactions:customer_list')


@login_required
def redirect_combined_voucher(request, customer_pk):
    """Redirect old combined voucher URL to transactions app"""
    return redirect('transactions:customer_list')
