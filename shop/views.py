from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse
from .models import ShopInfo, Product, Order, InventoryProduct, Invoice
from .forms import OrderForm, InventoryProductForm, InvoiceForm, PaymentForm, OrderPaymentForm
from decimal import Decimal


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
            Q(product_name__icontains=search_query)
        )

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
    """নতুন অর্ডার তৈরি"""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'অর্ডার সফলভাবে তৈরি হয়েছে!')
            return redirect('order_list')
    else:
        form = OrderForm()

    context = {'form': form}
    return render(request, 'admin_panel/order_form.html', context)


@login_required
def order_edit(request, pk):
    """অর্ডার সম্পাদনা"""
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            # Save other fields but preserve dates unless explicitly provided
            order_instance = form.save(commit=False)
            # If admin provided a new order_date, use it; otherwise keep existing
            new_order_date = form.cleaned_data.get('order_date')
            if new_order_date:
                order_instance.order_date = new_order_date
            else:
                order_instance.order_date = order.order_date

            new_delivery_date = form.cleaned_data.get('delivery_date')
            if new_delivery_date:
                order_instance.delivery_date = new_delivery_date
            else:
                order_instance.delivery_date = order.delivery_date

            order_instance.save()
            messages.success(request, 'অর্ডার সফলভাবে আপডেট হয়েছে!')
            return redirect('order_list')
    else:
        form = OrderForm(instance=order)

    context = {'form': form, 'order': order}
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
            Q(product_name__icontains=search_query)
        )

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



# ==================== ইনভয়েস/ভাউচার ব্যবস্থাপনা ====================

@login_required
def invoice_list(request):
    """ইনভয়েস তালিকা"""
    search_query = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)

    invoices = Invoice.objects.filter(is_latest=True)

    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(customer_name__icontains=search_query) |
            Q(mobile_number__icontains=search_query)
        )

    paginator = Paginator(invoices, 15)
    page_obj = paginator.get_page(page_number)

    context = {
        'invoices': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'admin_panel/invoice_list.html', context)


@login_required
def invoice_create(request):
    """নতুন ইনভয়েস তৈরি"""
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            try:
                invoice = form.save(commit=False)
                invoice.unit_price = invoice.product.price_per_unit
                invoice.save()
                messages.success(request, f'✅ ইনভয়েস {invoice.invoice_number} তৈরি হয়েছে!')
                return redirect('invoice_detail', pk=invoice.pk)
            except ValueError as e:
                messages.error(request, f'❌ {str(e)}')
    else:
        form = InvoiceForm()

    context = {'form': form}
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
    """ইনভয়েস এডিট (নতুন ভার্সন তৈরি)"""
    old_invoice = get_object_or_404(Invoice, pk=pk)

    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            try:
                # পুরাতন ইনভয়েসের স্টক ফেরত দেওয়া
                old_invoice.product.stock_quantity += old_invoice.quantity
                old_invoice.product.save()

                # নতুন ইনভয়েস তৈরি
                new_invoice = form.save(commit=False)
                new_invoice.unit_price = new_invoice.product.price_per_unit
                new_invoice.original_invoice = old_invoice.original_invoice or old_invoice
                new_invoice.save()

                # পুরাতন ইনভয়েস মার্ক করা
                old_invoice.is_latest = False
                old_invoice.save()

                messages.success(request, f'✅ নতুন ইনভয়েস {new_invoice.invoice_number} তৈরি হয়েছে! পুরাতন ইনভয়েস সংরক্ষিত আছে।')
                return redirect('invoice_detail', pk=new_invoice.pk)
            except ValueError as e:
                messages.error(request, f'❌ {str(e)}')
    else:
        # পুরাতন ডেটা দিয়ে ফর্ম পূরণ
        form = InvoiceForm(initial={
            'customer_name': old_invoice.customer_name,
            'mobile_number': old_invoice.mobile_number,
            'product': old_invoice.product,
            'quantity': old_invoice.quantity,
            'discount_percentage': old_invoice.discount_percentage,
            'paid_amount': old_invoice.paid_amount,
            'notes': old_invoice.notes,
            'sale_date': old_invoice.sale_date,  # বিক্রয়ের তারিখ যোগ করা হয়েছে
        })

    context = {
        'form': form,
        'old_invoice': old_invoice,
    }
    return render(request, 'admin_panel/invoice_form.html', context)


@login_required
def invoice_delete(request, pk):
    """ইনভয়েস/ভাউচার মুছে ফেলা"""
    invoice = get_object_or_404(Invoice, pk=pk)
    inv_number = invoice.invoice_number
    try:
        # স্টক ফেরত (বিক্রয় বাতিল হিসাবে)
        invoice.product.stock_quantity += invoice.quantity
        invoice.product.save()
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
                recipient_list=['aniklpu01@gmail.com'],
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
