from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Sum, Count, Q, Avg, F
from decimal import Decimal
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
)
from .forms import OrderForm, InventoryProductForm, InvoiceForm, PaymentForm, OrderPaymentForm, StockManagementForm
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


# কাস্টম অ্যাডমিন প্যানেল ভিউ
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
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    completed_orders = Order.objects.filter(status='completed', delivery_status='delivered').count()
    completed_not_delivered = Order.objects.filter(status='completed', delivery_status='not_delivered').count()

    # শুধু চলমান অর্ডার (সম্পন্ন অর্ডার দেখাবেন না)
    recent_orders = Order.objects.exclude(status='completed').order_by('status', '-created_at')[:10]

    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'completed_not_delivered': completed_not_delivered,
        'recent_orders': recent_orders,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
def order_list(request):
    """অর্ডার তালিকা - শুধু চলমান অর্ডার"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    # Dashboard: only ongoing/pending orders (completed orders appear only on completed page)
    orders = Order.objects.exclude(status='completed').order_by('status', '-created_at')

    if search_query:
        orders = orders.filter(
            Q(customer_name__icontains=search_query) |
            Q(mobile_number__icontains=search_query) |
            Q(items__product_name__icontains=search_query)
        ).distinct()

    if status_filter:
        orders = orders.filter(status=status_filter)

    context = {
        'orders': orders,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'admin_panel/order_list.html', context)


@login_required
def order_create(request):
    """নতুন অর্ডার তৈরি - একাধিক পণ্য সাপোর্ট"""
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
    }
    return render(request, 'admin_panel/order_form.html', context)


@login_required
def order_edit(request, pk):
    """অর্ডার সম্পাদনা - একাধিক পণ্য"""
    order = get_object_or_404(Order, pk=pk)

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

    context = {
        'form': form,
        'order': order,
        'products_json': products_json,
        'edit_items_json': json.dumps(existing_items),
    }
    return render(request, 'admin_panel/order_form.html', context)


@login_required
def order_delete(request, pk):
    """অর্ডার মুছে ফেলা"""
    order = get_object_or_404(Order, pk=pk)
    order.delete()
    messages.success(request, 'অর্ডার মুছে ফেলা হয়েছে!')
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

    context = {
        'order': order,
        'shop_info': shop_info,
    }
    return render(request, 'admin_panel/voucher.html', context)



# ==================== ইনভেন্টরি পণ্য ব্যবস্থাপনা ====================

@login_required
def inventory_product_list(request):
    """ইনভেন্টরি পণ্য তালিকা"""
    search_query = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)

    products = InventoryProduct.objects.all()

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    paginator = Paginator(products, 15)
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'admin_panel/inventory_product_list.html', context)


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
                if operation_type == 'add':
                    product.add_stock(quantity)
                    messages.success(request, f'✅ {quantity} {product.get_unit_display()} স্টক যোগ করা হয়েছে!')
                elif operation_type == 'remove':
                    product.remove_stock(quantity)
                    messages.success(request, f'✅ {quantity} {product.get_unit_display()} স্টক কমানো হয়েছে!')
                
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
    
    # Validate per_page
    try:
        per_page = int(per_page)
        if per_page not in [15, 50, 100, 200]:
            per_page = 15
    except ValueError:
        per_page = 15

    invoices = Invoice.objects.filter(is_latest=True)
    
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
        'total_count': total_count,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_due': total_due,
    }
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
    
    # তারিখ গণনা
    today = timezone.now().date()
    one_month_ago = today - timedelta(days=30)
    
    # পণ্য স্ট্যাটিস্টিক্স
    total_products = InventoryProduct.objects.count()
    active_products = InventoryProduct.objects.filter(is_active=True).count()
    inactive_products = total_products - active_products
    
    # মোট পণ্যের মূল্য (স্টক × ইউনিট প্রাইস)
    total_inventory_value = InventoryProduct.objects.filter(
        is_active=True
    ).aggregate(
        total_value=Sum(F('stock_quantity') * F('price_per_unit'))
    )['total_value'] or Decimal('0')
    
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
    
    # টপ ১০ সবচেয়ে বেশি মূল্যের পণ্য
    top_valuable_products = InventoryProduct.objects.filter(
        is_active=True
    ).order_by(
        -(F('stock_quantity') * F('price_per_unit'))
    )[:10]
    
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
    """বাকি খাতা - সব অর্ডার যেগুলোর বাকি আছে"""
    search_query = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)
    
    # Get all orders with due amounts (both from Order and Invoice models)
    orders_with_due = Order.objects.filter(due_amount__gt=0).order_by('-created_at')
    invoices_with_due = Invoice.objects.filter(due_amount__gt=0, is_latest=True).order_by('-created_at')
    
    # Combine and search
    if search_query:
        orders_with_due = orders_with_due.filter(
            Q(customer_name__icontains=search_query) |
            Q(mobile_number__icontains=search_query)
        )
        invoices_with_due = invoices_with_due.filter(
            Q(customer_name__icontains=search_query) |
            Q(mobile_number__icontains=search_query)
        )
    
    # Create combined list with type information
    due_items = []
    
    # Add orders
    for order in orders_with_due:
        due_items.append({
            'type': 'order',
            'id': order.pk,
            'customer_name': order.customer_name,
            'mobile_number': order.mobile_number,
            'total_amount': order.total_price,
            'paid_amount': order.cash_paid,
            'due_amount': order.due_amount,
            'date': order.order_date,
            'created_at': order.created_at,
            'status': order.status,
            'delivery_status': order.delivery_status,
        })
    
    # Add invoices
    for invoice in invoices_with_due:
        # Calculate actual paid amount from payments if they exist
        total_paid = sum(p.amount for p in invoice.payments.all()) if invoice.payments.exists() else invoice.paid_amount
        actual_due = invoice.total_amount - total_paid
        
        if actual_due > 0:  # Only show if there's actually due
            due_items.append({
                'type': 'invoice',
                'id': invoice.pk,
                'customer_name': invoice.customer_name,
                'mobile_number': invoice.mobile_number,
                'total_amount': invoice.total_amount,
                'paid_amount': total_paid,
                'due_amount': actual_due,
                'date': invoice.sale_date,
                'created_at': invoice.created_at,
                'invoice_number': invoice.invoice_number,
            })
    
    # Sort by created_at (newest first)
    due_items.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Calculate totals
    total_amount = sum(item['total_amount'] for item in due_items)
    total_paid = sum(item['paid_amount'] for item in due_items)
    total_due = sum(item['due_amount'] for item in due_items)
    
    # Pagination - 100 items per page
    paginator = Paginator(due_items, 100)
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


# ==================== কাস্টমার লিস্ট (Customer List) ====================

@login_required
def customer_list(request):
    """কাস্টমার লিস্ট - সব কাস্টমারের তথ্য (শুধু সুপার অ্যাডমিনের জন্য)"""
    if not request.user.is_superuser:
        messages.error(request, '❌ এই পেজে প্রবেশাধিকার নেই! শুধুমাত্র অ্যাডমিনের জন্য।')
        return redirect('admin_dashboard')
    
    search_query = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)
    
    # Get all unique customers from both Order and Invoice models
    order_customers = Order.objects.values('customer_name', 'mobile_number').distinct()
    invoice_customers = Invoice.objects.filter(is_latest=True).values('customer_name', 'mobile_number').distinct()
    
    # Combine unique customers
    all_customers = {}
    
    # Process order customers
    for customer in order_customers:
        key = (customer['customer_name'], customer['mobile_number'])
        if key not in all_customers:
            all_customers[key] = {
                'customer_name': customer['customer_name'],
                'mobile_number': customer['mobile_number'],
                'total_orders': 0,
                'total_invoices': 0,
                'total_order_amount': 0,
                'total_invoice_amount': 0,
                'total_order_paid': 0,
                'total_invoice_paid': 0,
                'total_order_due': 0,
                'total_invoice_due': 0,
                'last_order_date': None,
                'last_invoice_date': None,
            }
    
    # Process invoice customers
    for customer in invoice_customers:
        key = (customer['customer_name'], customer['mobile_number'])
        if key not in all_customers:
            all_customers[key] = {
                'customer_name': customer['customer_name'],
                'mobile_number': customer['mobile_number'],
                'total_orders': 0,
                'total_invoices': 0,
                'total_order_amount': 0,
                'total_invoice_amount': 0,
                'total_order_paid': 0,
                'total_invoice_paid': 0,
                'total_order_due': 0,
                'total_invoice_due': 0,
                'last_order_date': None,
                'last_invoice_date': None,
            }
    
    # Calculate statistics for each customer
    for key, customer_data in all_customers.items():
        name, mobile = key
        
        # Order statistics
        orders = Order.objects.filter(customer_name=name, mobile_number=mobile)
        customer_data['total_orders'] = orders.count()
        customer_data['total_order_amount'] = orders.aggregate(total=Sum('total_price'))['total'] or 0
        customer_data['total_order_paid'] = orders.aggregate(total=Sum('cash_paid'))['total'] or 0
        customer_data['total_order_due'] = orders.aggregate(total=Sum('due_amount'))['total'] or 0
        
        # Get last order date
        last_order = orders.order_by('-created_at').first()
        if last_order:
            customer_data['last_order_date'] = last_order.created_at
        
        # Invoice statistics
        invoices = Invoice.objects.filter(customer_name=name, mobile_number=mobile, is_latest=True)
        customer_data['total_invoices'] = invoices.count()
        customer_data['total_invoice_amount'] = invoices.aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Calculate actual paid amounts from payments
        total_invoice_paid = 0
        total_invoice_due = 0
        for invoice in invoices:
            invoice_paid = sum(p.amount for p in invoice.payments.all()) if invoice.payments.exists() else invoice.paid_amount
            total_invoice_paid += invoice_paid
            total_invoice_due += (invoice.total_amount - invoice_paid)
        
        customer_data['total_invoice_paid'] = total_invoice_paid
        customer_data['total_invoice_due'] = total_invoice_due
        
        # Get last invoice date
        last_invoice = invoices.order_by('-created_at').first()
        if last_invoice:
            customer_data['last_invoice_date'] = last_invoice.created_at
        
        # Calculate totals
        customer_data['total_amount'] = customer_data['total_order_amount'] + customer_data['total_invoice_amount']
        customer_data['total_paid'] = customer_data['total_order_paid'] + customer_data['total_invoice_paid']
        customer_data['total_due'] = customer_data['total_order_due'] + customer_data['total_invoice_due']
        
        # Determine last buy date
        if customer_data['last_order_date'] and customer_data['last_invoice_date']:
            customer_data['last_buy_date'] = max(customer_data['last_order_date'], customer_data['last_invoice_date'])
        elif customer_data['last_order_date']:
            customer_data['last_buy_date'] = customer_data['last_order_date']
        elif customer_data['last_invoice_date']:
            customer_data['last_buy_date'] = customer_data['last_invoice_date']
        else:
            customer_data['last_buy_date'] = None
    
    # Convert to list and apply search filter
    customers_list = list(all_customers.values())
    
    if search_query:
        customers_list = [
            customer for customer in customers_list
            if search_query.lower() in customer['customer_name'].lower() 
            or search_query in customer['mobile_number']
        ]
    
    # Sort by last buy date (most recent first)
    customers_list.sort(key=lambda x: x['last_buy_date'] or timezone.datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    
    # Calculate totals for all customers
    total_amount = sum(c['total_amount'] for c in customers_list)
    total_paid = sum(c['total_paid'] for c in customers_list)
    total_due = sum(c['total_due'] for c in customers_list)
    
    # Pagination
    paginator = Paginator(customers_list, 50)  # 50 customers per page
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customers': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_due': total_due,
    }
    return render(request, 'admin_panel/customer_list.html', context)