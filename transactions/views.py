from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Customer, Transaction, TransactionItem, TransactionHistory, CustomerSubmission, CustomerItem, CustomerNote
from .forms import CustomerForm, TransactionSubmissionForm, TransactionPurchaseForm, TransactionWithdrawalForm, CustomerNoteForm
from shop.models import InventoryProduct, StockHistory


# ==================== Order Management ====================

@login_required
def order_create(request):
    """Create new order - select customer and create purchase transaction"""
    # Get all customers for selection
    customers = Customer.objects.all().order_by('name')
    
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        
        if not customer_id:
            messages.error(request, '❌ Please select a customer!')
        else:
            try:
                customer = Customer.objects.get(pk=customer_id)
                # Redirect to purchase creation for this customer
                return redirect('transaction_purchase_create', customer_pk=customer.pk)
            except Customer.DoesNotExist:
                messages.error(request, '❌ Customer not found!')
    
    context = {
        'customers': customers,
        'page_title': 'Create New Order',
    }
    return render(request, 'transactions/order_create.html', context)


@login_required
def import_legacy_orders(request):
    """Import customers and orders from custom order system to transaction system"""
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
                call_command('import_legacy_orders', dry_run=True)
                result = output.getvalue()
                messages.success(request, '✅ Dry run completed. Check the output below.')
            except Exception as e:
                messages.error(request, f'❌ Error during dry run: {str(e)}')
                result = str(e)
            finally:
                sys.stdout = sys.__stdout__
            
            context = {
                'page_title': 'Import Legacy Orders to Transaction System',
                'result': result,
                'is_dry_run': True,
            }
            return render(request, 'transactions/import_legacy_orders.html', context)
        
        elif action == 'import':
            # Actual import
            try:
                call_command('import_legacy_orders')
                messages.success(request, '✅ Import completed successfully!')
                return redirect('customer_list')
            except Exception as e:
                messages.error(request, f'❌ Error during import: {str(e)}')
    
    # GET request - show import page
    # Get statistics
    from shop.models import Customer as LegacyCustomer, Order
    total_customers = LegacyCustomer.objects.count()
    total_orders = Order.objects.count()
    transaction_customers = Customer.objects.count()
    
    # Count customers that would be imported (not already in transaction system)
    customers_to_import = 0
    for customer in LegacyCustomer.objects.all():
        if not Customer.objects.filter(mobile_number=customer.mobile_number).exists():
            customers_to_import += 1
    
    context = {
        'page_title': 'Import Legacy Orders to Transaction System',
        'total_customers': total_customers,
        'total_orders': total_orders,
        'transaction_customers': transaction_customers,
        'customers_to_import': customers_to_import,
    }
    return render(request, 'transactions/import_legacy_orders.html', context)


# ==================== Customer Management ====================

@login_required
def customer_list(request):
    """Transaction customer list with filtering by transaction status"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    delivery_status_filter = request.GET.get('delivery_status', '')
    
    # Get pagination size from request, default to 20
    per_page = request.GET.get('per_page', '20')
    try:
        per_page = int(per_page)
        if per_page not in [20, 50, 100, 200]:
            per_page = 20
    except (ValueError, TypeError):
        per_page = 20
    
    # Get all customers
    customers = Customer.objects.filter(is_deleted=False).order_by('-created_at')
    
    # If status filter is provided, filter customers by their transactions
    if status_filter or delivery_status_filter:
        # Get transactions matching the filters
        transactions = Transaction.objects.all()
        
        if status_filter:
            transactions = transactions.filter(status=status_filter)
        
        if delivery_status_filter:
            transactions = transactions.filter(delivery_status=delivery_status_filter)
        
        # Get unique customers from filtered transactions
        customer_ids = list(transactions.values_list('customer_id', flat=True).distinct())
        customers = customers.filter(pk__in=customer_ids)
    
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) | Q(mobile_number__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(customers, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'customers': page_obj.object_list,
        'search_query': search_query,
        'status_filter': status_filter,
        'delivery_status_filter': delivery_status_filter,
        'total_customers': customers.count(),
        'per_page': per_page,
    }
    return render(request, 'transactions/customer_list.html', context)


@login_required
def customer_create(request):
    """Create new customer"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'✅ {customer.name} successfully added!')
            return redirect('transactions:customer_detail', pk=customer.pk)
    else:
        form = CustomerForm()
    
    context = {
        'form': form,
        'page_title': 'Create New Customer',
    }
    return render(request, 'transactions/customer_form.html', context)


@login_required
def customer_detail(request, pk):
    """Customer detail - transaction based"""
    customer = get_object_or_404(Customer, pk=pk)
    
    # Get all ACTIVE transactions (non-deleted, non-reversed) excluding reversal type transactions
    transactions = customer.transactions.filter(
        is_deleted=False,
        is_reversed=False
    ).exclude(
        transaction_type='reversal'
    ).order_by('-created_at')
    
    # Get transaction counts
    submission_count = transactions.filter(transaction_type='submission').count()
    purchase_count = transactions.filter(transaction_type='purchase').count()
    withdrawal_count = transactions.filter(transaction_type='withdrawal').count()
    
    # Calculate total cash paid from ACTIVE purchase transactions only
    total_cash_paid = Decimal('0')
    purchase_transactions = transactions.filter(transaction_type='purchase')
    for purchase in purchase_transactions:
        total_cash_paid += purchase.cash_paid
    
    context = {
        'customer': customer,
        'transactions': transactions[:10],  # Show last 10
        'total_transactions': transactions.count(),
        'submission_count': submission_count,
        'purchase_count': purchase_count,
        'withdrawal_count': withdrawal_count,
        'total_cash_paid': total_cash_paid,
    }
    return render(request, 'transactions/customer_detail.html', context)


@login_required
def customer_edit(request, pk):
    """Edit customer"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            old_name = customer.name
            old_mobile = customer.mobile_number
            old_address = customer.address
            
            customer = form.save()
            
            # Record history
            TransactionHistory.objects.create(
                transaction=None,  # Customer edit, not transaction
                action='edited',
                old_balance=customer.current_balance,
                new_balance=customer.current_balance,
                notes=f'Customer edit: Name {old_name} → {customer.name}, Mobile {old_mobile} → {customer.mobile_number}',
                performed_by=request.user
            )
            
            messages.success(request, f'✅ {customer.name} successfully updated!')
            return redirect('customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)
    
    context = {
        'form': form,
        'customer': customer,
        'page_title': f'{customer.name} - Edit',
    }
    return render(request, 'transactions/customer_form.html', context)


@login_required
def customer_delete(request, pk):
    """Delete customer and all associated transactions"""
    customer = get_object_or_404(Customer, pk=pk)
    
    # Check if customer has transactions
    has_transactions = customer.transactions.exists()
    transaction_count = customer.transactions.count() if has_transactions else 0
    
    # For POST requests (from form submission) - delete everything
    if request.method == 'POST':
        name = customer.name
        # Soft delete customer and all his transactions
        customer.is_deleted = True
        customer.deleted_at = timezone.now()
        customer.save()
        
        # Soft delete all transactions
        if has_transactions:
            customer.transactions.all().update(is_deleted=True, deleted_at=timezone.now())
        
        messages.success(request, f'✅ {name} successfully moved to trash!')
        
        return redirect('transactions:customer_list')
    
    # Show confirmation page for GET requests
    context = {
        'customer': customer,
        'has_transactions': has_transactions,
        'transaction_count': transaction_count,
    }
    return render(request, 'transactions/customer_delete.html', context)


@login_required
def customer_bulk_delete(request):
    """Bulk delete customers"""
    if request.method != 'POST':
        messages.error(request, '❌ Invalid request')
        return redirect('customer_list')
    
    selected_ids = request.POST.getlist('selected_customers')
    
    if not selected_ids:
        messages.error(request, '❌ No customers selected')
        return redirect('customer_list')
    
    deleted_count = 0
    failed_count = 0
    
    for customer_id in selected_ids:
        try:
            customer = Customer.objects.get(pk=customer_id)
            
            # Check if customer has transactions
            if customer.transactions.exists():
                failed_count += 1
                continue
            
            name = customer.name
            customer.delete()
            deleted_count += 1
        except Customer.DoesNotExist:
            failed_count += 1
            continue
    
    if deleted_count > 0:
        messages.success(request, f'✅ {deleted_count} customers successfully deleted!')
    
    if failed_count > 0:
        messages.warning(request, f'⚠️ {failed_count} customers could not be deleted (may have transactions)')
    
    return redirect('customer_list')


@login_required
def customer_trash_list(request):
    """View to list soft-deleted customers"""
    trashed_customers = Customer.objects.filter(is_deleted=True).order_by('-deleted_at')
    context = {'customers': trashed_customers, 'page_title': 'Deleted Customers'}
    return render(request, 'transactions/customer_trash_list.html', context)


@login_required
def customer_restore(request, pk):
    """Restore a soft-deleted customer"""
    customer = get_object_or_404(Customer, pk=pk, is_deleted=True)
    
    if request.method == 'POST':
        customer.is_deleted = False
        customer.deleted_at = None
        customer.save()
        
        # Restore transactions
        customer.transactions.filter(is_deleted=True).update(is_deleted=False, deleted_at=None)
        
        messages.success(request, f'✅ {customer.name} and their transactions restored!')
        return redirect('transactions:customer_trash_list')
    
    context = {'customer': customer}
    return render(request, 'transactions/customer_restore_confirm.html', context)


# ==================== Transaction Management ====================

@login_required
def transaction_submission_create(request, customer_pk):
    """Transaction - create submission (deposit)"""
    customer = get_object_or_404(Customer, pk=customer_pk)
    
    if request.method == 'POST':
        form = TransactionSubmissionForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            order_date = form.cleaned_data.get('order_date')
            notes = form.cleaned_data.get('notes', '')
            
            # Create transaction
            transaction = Transaction.objects.create(
                customer=customer,
                transaction_type='submission',
                amount=amount,
                order_date=order_date,
                notes=notes,
                status='pending',
                delivery_status='not_delivered',
                created_by=request.user
            )
            
            # Record history
            TransactionHistory.objects.create(
                transaction=transaction,
                action='created',
                old_balance=transaction.balance_before,
                new_balance=transaction.balance_after,
                notes=f'Submission created: ৳{amount}',
                performed_by=request.user
            )
            
            messages.success(request, f'✅ ৳{amount} submission successfully added! Transaction #: {transaction.transaction_number}')
            return redirect('transactions:transaction_voucher', pk=transaction.pk)
    else:
        form = TransactionSubmissionForm()
    
    context = {
        'form': form,
        'customer': customer,
        'page_title': f'{customer.name} - New Submission',
    }
    return render(request, 'transactions/transaction_submission_form.html', context)


@login_required
def transaction_purchase_create(request, customer_pk):
    """Transaction - create purchase (multiple items + discount support)"""
    customer = get_object_or_404(Customer, pk=customer_pk)
    
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
    
    # Status choices for template
    status_choices = Transaction.STATUS_CHOICES
    delivery_status_choices = Transaction.DELIVERY_STATUS_CHOICES
    
    if request.method == 'POST':
        items_json_str = request.POST.get('items_json', '[]')
        total_discount = request.POST.get('total_discount', '0')
        cash_paid = request.POST.get('cash_paid', '0')
        order_date = request.POST.get('order_date', '')
        delivery_date = request.POST.get('delivery_date', '')
        payment_date = request.POST.get('payment_date', '')
        
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
        
        # Convert cash paid
        try:
            cash_paid = Decimal(str(cash_paid))
            if cash_paid < 0:
                cash_paid = Decimal('0')
        except:
            cash_paid = Decimal('0')
        
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
            messages.error(request, '❌ Please add at least one item!')
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
                        raise ValueError("Please enter product name")
                    if quantity <= 0:
                        raise ValueError(f"{product_name}: Quantity must be greater than 0")
                    if unit_price <= 0:
                        raise ValueError(f"{product_name}: Price must be greater than 0")
                    if item_discount < 0 or item_discount > 100:
                        raise ValueError(f"{product_name}: Discount must be between 0-100%")
                    
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
                
                # Calculate due amount - NEVER negative
                # If cash_paid > final_total, due_amount = 0 (fully paid)
                # Extra money goes to deposit, doesn't reduce due_amount below 0
                due_amount = max(final_total - cash_paid, Decimal('0'))
                
                # ALWAYS record actual cash paid, even if it's more than final total
                # Extra money will create a separate submission transaction
                actual_cash_for_purchase = min(cash_paid, final_total)
                
                # If cash paid is more than final total, create submission for extra amount
                extra_submission = None
                if cash_paid > final_total:
                    extra_amount = cash_paid - final_total
                    extra_submission = Transaction.objects.create(
                        customer=customer,
                        transaction_type='submission',
                        amount=extra_amount,
                        notes=f'অতিরিক্ত জমা (ক্রয় লেনদেন থেকে): ৳{extra_amount}',
                        status='completed',
                        delivery_status='not_delivered',
                        created_by=request.user,
                        order_date=order_date_obj
                    )
                    
                    # Record history for extra submission
                    TransactionHistory.objects.create(
                        transaction=extra_submission,
                        action='created',
                        old_balance=extra_submission.balance_before,
                        new_balance=extra_submission.balance_after,
                        notes=f'অতিরিক্ত জমা: ৳{extra_amount} (ক্রয় লেনদেন থেকে)',
                        performed_by=request.user
                    )
                
                # Create main transaction
                item_names = ', '.join([item['product_name'] for item in validated_items])
                transaction = Transaction.objects.create(
                    customer=customer,
                    transaction_type='purchase',
                    amount=final_total,
                    cash_paid=actual_cash_for_purchase,
                    due_amount=due_amount,
                    item_name=item_names,
                    item_description=f'{len(validated_items)} items purchased',
                    item_quantity=sum(item['quantity'] for item in validated_items),
                    item_unit_price=final_total / sum(item['quantity'] for item in validated_items) if sum(item['quantity'] for item in validated_items) > 0 else Decimal('0'),
                    gross_amount=subtotal + total_discount_amount,
                    item_discount_percentage=total_discount,
                    item_discount_amount=total_discount_amount,
                    total_discount_percentage=total_discount,
                    total_discount_amount=total_discount_amount,
                    notes=request.POST.get('notes', '') + (f'\n\nনগদ পরিশোধ: ৳{cash_paid}' if cash_paid > 0 else ''),
                    status='pending',
                    delivery_status='not_delivered',
                    created_by=request.user,
                    order_date=order_date_obj,
                    delivery_date=delivery_date_obj
                )
                
                # Create transaction items for each product
                for item in validated_items:
                    TransactionItem.objects.create(
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
                            notes=f'Transaction - {customer.name} ({transaction.transaction_number})'
                        )
                
                messages.success(request, f'✅ Purchase successful! মোট: ৳{final_total}, নগদ: ৳{cash_paid}, বাকি: ৳{due_amount if due_amount > 0 else 0} | Transaction #: {transaction.transaction_number}')
                return redirect('transactions:transaction_voucher', pk=transaction.pk)
                
            except ValueError as e:
                messages.error(request, f'❌ {str(e)}')
            except Exception as e:
                messages.error(request, f'❌ Error: {str(e)}')
    
    context = {
        'form': None,  # No form needed, using custom template
        'customer': customer,
        'page_title': f'{customer.name} - New Purchase',
        'products_json': products_json,
        'today': today,
        'delivery_date': default_delivery_date,
        'status_choices': status_choices,
        'delivery_status_choices': delivery_status_choices,
    }
    return render(request, 'transactions/transaction_purchase_form.html', context)


@login_required
def transaction_withdrawal_create(request, customer_pk):
    """Transaction - create withdrawal"""
    customer = get_object_or_404(Customer, pk=customer_pk)
    
    if request.method == 'POST':
        form = TransactionWithdrawalForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            order_date = form.cleaned_data.get('order_date')
            notes = form.cleaned_data.get('notes', '')
            
            # Create transaction (amount is negative for withdrawal)
            transaction = Transaction.objects.create(
                customer=customer,
                transaction_type='withdrawal',
                amount=amount,
                order_date=order_date,
                notes=notes,
                status='completed',
                created_by=request.user
            )
            
            # Record history
            TransactionHistory.objects.create(
                transaction=transaction,
                action='created',
                old_balance=transaction.balance_before,
                new_balance=transaction.balance_after,
                notes=f'Withdrawal created: ৳{amount}',
                performed_by=request.user
            )
            
            messages.success(request, f'✅ ৳{amount} withdrawal successful! Transaction #: {transaction.transaction_number}')
            return redirect('transactions:transaction_voucher', pk=transaction.pk)
    else:
        form = TransactionWithdrawalForm()
    
    context = {
        'form': form,
        'customer': customer,
        'page_title': f'{customer.name} - Withdraw Money',
    }
    return render(request, 'transactions/transaction_withdrawal_form.html', context)


# ==================== Transaction Voucher & List ====================

@login_required
def transaction_voucher(request, pk):
    """Transaction voucher"""
    transaction = get_object_or_404(Transaction, pk=pk)
    
    # Get shop info
    from shop.models import ShopInfo
    shop_info = ShopInfo.objects.first()
    
    context = {
        'transaction': transaction,
        'customer': transaction.customer,
        'shop_info': shop_info,
    }
    return render(request, 'transactions/transaction_voucher.html', context)


@login_required
def transaction_list_all(request):
    """Transaction list - all transactions with filtering"""
    status_filter = request.GET.get('status', '')
    delivery_status_filter = request.GET.get('delivery_status', '')
    transaction_type = request.GET.get('type', '')
    search_query = request.GET.get('search', '')
    
    # Get pagination size from request, default to 50
    per_page = request.GET.get('per_page', '50')
    try:
        per_page = int(per_page)
        if per_page not in [20, 50, 100, 200]:
            per_page = 50
    except (ValueError, TypeError):
        per_page = 50
    
    # Get all transactions
    transactions = Transaction.objects.filter(is_deleted=False).order_by('-created_at')
    
    # Apply filters
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    if delivery_status_filter:
        transactions = transactions.filter(delivery_status=delivery_status_filter)
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if search_query:
        transactions = transactions.filter(
            Q(customer__name__icontains=search_query) | 
            Q(customer__mobile_number__icontains=search_query) |
            Q(transaction_number__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(transactions, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'transactions': page_obj.object_list,
        'status_filter': status_filter,
        'delivery_status_filter': delivery_status_filter,
        'transaction_type': transaction_type,
        'search_query': search_query,
        'total_transactions': transactions.count(),
        'per_page': per_page,
    }
    return render(request, 'transactions/transaction_list_all.html', context)


@login_required
def transaction_list(request, customer_pk):
    """Transaction list - for specific customer"""
    customer = get_object_or_404(Customer, pk=customer_pk)
    
    transaction_type = request.GET.get('type', '')
    date_from = request.GET.get('from_date', '')
    date_to = request.GET.get('to_date', '')
    
    # Show all non-reversed transactions (including pending, ready, completed, cancelled)
    transactions = customer.transactions.filter(is_reversed=False).order_by('-created_at')
    
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
    return render(request, 'transactions/transaction_list.html', context)


@login_required
def transaction_complete(request, pk):
    """Mark purchase transaction as completed (delivered)"""
    transaction = get_object_or_404(Transaction, pk=pk)
    
    # Only allow completing purchase transactions
    if transaction.transaction_type != 'purchase':
        messages.error(request, '❌ শুধুমাত্র ক্রয় লেনদেন সম্পন্ন করা যায়!')
        return redirect('transactions:customer_detail', pk=transaction.customer.pk)
    
    # Don't allow completing reversed transactions
    if transaction.is_reversed:
        messages.error(request, '❌ বাতিলকৃত লেনদেন সম্পন্ন করা যায় না!')
        return redirect('transactions:customer_detail', pk=transaction.customer.pk)
    
    # Check if already completed
    if transaction.delivery_status == 'delivered':
        messages.info(request, 'ℹ️ এই অর্ডার ইতিমধ্যে সম্পন্ন হয়েছে!')
        return redirect('transactions:customer_detail', pk=transaction.customer.pk)
    
    # Mark as completed
    transaction.delivery_status = 'delivered'
    transaction.status = 'completed'
    transaction.save()
    
    # Record history
    TransactionHistory.objects.create(
        transaction=transaction,
        action='completed',
        old_balance=transaction.customer.current_balance,
        new_balance=transaction.customer.current_balance,
        notes=f'অর্ডার সম্পন্ন: {transaction.transaction_number}',
        performed_by=request.user
    )
    
    messages.success(request, f'✅ অর্ডার সম্পন্ন হয়েছে! লেনদেন #: {transaction.transaction_number}')
    return redirect('transactions:customer_detail', pk=transaction.customer.pk)


@login_required
def transaction_reverse(request, pk):
    """Reverse/cancel transaction or restore it"""
    # Allow reversing even if trashed? Usually not. Let's find it but ensure customer isn't deleted.
    transaction = get_object_or_404(Transaction, pk=pk)
    
    if transaction.customer.is_deleted:
        messages.error(request, '❌ এই কাস্টমার বর্তমানে ট্র্যাশে আছে।')
        return redirect('transactions:customer_list')

    if request.method == 'POST':
        old_balance = transaction.customer.current_balance
        
        # Check if this is a restore action (undo cancellation)
        if transaction.is_reversed:
            # RESTORE: Mark as not reversed
            # Restore inventory stock if it was a purchase
            if transaction.transaction_type == 'purchase':
                for item in transaction.items.all():
                    if item.inventory_product:
                        item.inventory_product.remove_stock(item.quantity)
                        
                        # Create stock history
                        StockHistory.objects.create(
                            product=item.inventory_product,
                            operation='sale',
                            quantity=item.quantity,
                            previous_quantity=item.inventory_product.stock_quantity + item.quantity,
                            new_quantity=item.inventory_product.stock_quantity,
                            notes=f'Transaction restored: {transaction.transaction_number}'
                        )
            
            # Mark as not reversed - the model's save() will recalculate balance
            transaction.is_reversed = False
            transaction.save()
            
            # Get the new balance after model recalculated it
            transaction.customer.refresh_from_db()
            new_balance = transaction.customer.current_balance
            
            # Record history
            TransactionHistory.objects.create(
                transaction=transaction,
                action='edited',
                old_balance=old_balance,
                new_balance=new_balance,
                notes=f'Transaction restored: {transaction.transaction_number}',
                performed_by=request.user
            )
            
            messages.success(request, f'✅ Transaction restored successfully! {transaction.transaction_number}')
        else:
            # CANCEL: Mark as reversed
            # Restore inventory stock if it was a purchase
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
                            notes=f'Transaction cancelled: {transaction.transaction_number}'
                        )
            
            # Mark as reversed - the model's save() will recalculate balance
            transaction.is_reversed = True
            transaction.save()
            
            # Get the new balance after model recalculated it
            transaction.customer.refresh_from_db()
            new_balance = transaction.customer.current_balance
            
            # Record history
            TransactionHistory.objects.create(
                transaction=transaction,
                action='reversed',
                old_balance=old_balance,
                new_balance=new_balance,
                notes=f'Transaction cancelled: {transaction.transaction_number}',
                performed_by=request.user
            )
            
            messages.success(request, f'✅ Transaction cancelled successfully! {transaction.transaction_number}')
        
        return redirect('transactions:customer_detail', pk=transaction.customer.pk)
    
    context = {
        'transaction': transaction,
        'customer': transaction.customer,
    }
    return render(request, 'transactions/transaction_reverse_confirm.html', context)


@login_required
def customer_statement(request, customer_pk):
    """Customer statement - complete transaction history with date filtering"""
    customer = get_object_or_404(Customer, pk=customer_pk)
    
    date_from = request.GET.get('from_date', '')
    date_to = request.GET.get('to_date', '')
    
    # Use order_date for filtering instead of created_at to preserve original order dates
    # Exclude deleted transactions and reversed transactions
    # Include ALL valid transactions (pending, completed, etc.) except deleted and reversed ones
    transactions = customer.transactions.filter(is_deleted=False, is_reversed=False).order_by('order_date')
    
    # Parse dates if provided
    from_date_obj = None
    to_date_obj = None
    
    if date_from:
        try:
            from_date_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            transactions = transactions.filter(order_date__gte=from_date_obj)
        except ValueError:
            date_from = ''
    
    if date_to:
        try:
            to_date_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            transactions = transactions.filter(order_date__lte=to_date_obj)
        except ValueError:
            date_to = ''
    
    # Calculate running balance
    running_balance = Decimal('0')
    transactions_with_balance = []
    
    for txn in transactions:
        running_balance = txn.balance_after
        transactions_with_balance.append({
            'transaction': txn,
            'running_balance': running_balance
        })
    
    # Calculate totals
    total_submitted = transactions.filter(transaction_type='submission').aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    total_purchased = transactions.filter(transaction_type='purchase').aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    total_withdrawn = transactions.filter(transaction_type='withdrawal').aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    
    context = {
        'customer': customer,
        'transactions': transactions,
        'transactions_with_balance': transactions_with_balance,
        'date_from': date_from,
        'date_to': date_to,
        'from_date_obj': from_date_obj,
        'to_date_obj': to_date_obj,
        'today': timezone.now().date(),
        'now': timezone.now(),
        'total_submitted': total_submitted,
        'total_purchased': total_purchased,
        'total_withdrawn': total_withdrawn,
        'net_balance': total_submitted - total_purchased - total_withdrawn,
    }
    return render(request, 'transactions/customer_statement.html', context)


@login_required
def customer_history(request, customer_pk):
    """Customer complete history - all actions"""
    customer = get_object_or_404(Customer, pk=customer_pk)
    
    # Get all history records for this customer's transactions
    history_records = TransactionHistory.objects.filter(
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
    return render(request, 'transactions/customer_history.html', context)


@login_required
def transaction_edit(request, pk):
    """Edit transaction - purchase edit"""
    transaction = get_object_or_404(Transaction, pk=pk)
    
    # Only allow editing purchase transactions
    if transaction.transaction_type != 'purchase':
        messages.error(request, '❌ Only purchase transactions can be edited!')
        return redirect('customer_detail', pk=transaction.customer.pk)
    
    # Don't allow editing reversed transactions
    if transaction.is_reversed:
        messages.error(request, '❌ Reversed transactions cannot be edited!')
        return redirect('customer_detail', pk=transaction.customer.pk)
    
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
            messages.error(request, '❌ Please add at least one item!')
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
                        raise ValueError("Please enter product name")
                    if quantity <= 0:
                        raise ValueError(f"{product_name}: Quantity must be greater than 0")
                    if unit_price <= 0:
                        raise ValueError(f"{product_name}: Price must be greater than 0")
                    if item_discount < 0 or item_discount > 100:
                        raise ValueError(f"{product_name}: Discount must be between 0-100%")
                    
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
                
                # Update status fields
                status = request.POST.get('status', 'completed')
                delivery_status = request.POST.get('delivery_status', 'not_delivered')
                transaction.status = status
                transaction.delivery_status = delivery_status
                
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
                    TransactionItem.objects.create(
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
                            raise ValueError(f"{item['product_name']}: Insufficient stock! Current: {inv_product.stock_quantity} {inv_product.get_unit_display()}, Required: {item['quantity']}")
                        
                        # Deduct stock
                        previous_stock = inv_product.stock_quantity
                        inv_product.remove_stock(item['quantity'])
                        StockHistory.objects.create(
                            product=inv_product,
                            operation='sale',
                            quantity=item['quantity'],
                            previous_quantity=previous_stock,
                            new_quantity=inv_product.stock_quantity,
                            notes=f'Transaction edit - {customer.name} ({transaction.transaction_number})'
                        )
                
                # Record history
                TransactionHistory.objects.create(
                    transaction=transaction,
                    action='edited',
                    old_balance=transaction.balance_before,
                    new_balance=transaction.balance_after,
                    notes=f'Purchase edited: {item_names}',
                    performed_by=request.user
                )
                
                messages.success(request, f'✅ Purchase successfully updated! ৳{final_total} | Transaction #: {transaction.transaction_number}')
                return redirect('transactions:transaction_voucher', pk=transaction.pk)
                
            except ValueError as e:
                messages.error(request, f'❌ {str(e)}')
            except Exception as e:
                messages.error(request, f'❌ Error: {str(e)}')
    
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
        'page_title': f'{customer.name} - Edit Purchase',
        'products_json': products_json,
        'edit_items_json': json.dumps(existing_items),
        'total_discount': float(transaction.total_discount_percentage),
    }
    return render(request, 'transactions/transaction_purchase_form.html', context)


# ==================== API Endpoints ====================

@login_required
def customer_search_api(request):
    """API endpoint for customer autocomplete search"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'customers': []})
    
    # Search in both Customer models
    from shop.models import Customer as LegacyCustomer
    customers = LegacyCustomer.objects.filter(
        Q(name__icontains=query) | Q(mobile_number__icontains=query)
    )[:10]
    
    transaction_customers = Customer.objects.filter(
        Q(name__icontains=query) | Q(mobile_number__icontains=query)
    )[:10]
    
    results = []
    
    # Add legacy customers
    for customer in customers:
        results.append({
            'id': customer.pk,
            'name': customer.name,
            'mobile': customer.mobile_number,
            'type': 'legacy_customer',
            'balance': float(customer.deposit_balance) if hasattr(customer, 'deposit_balance') else 0
        })
    
    # Add transaction customers
    for customer in transaction_customers:
        results.append({
            'id': customer.pk,
            'name': customer.name,
            'mobile': customer.mobile_number,
            'type': 'customer',
            'balance': float(customer.current_balance)
        })
    
    return JsonResponse({'customers': results})


@login_required
@csrf_exempt
def customer_notes_api(request, customer_pk):
    """API endpoint to get customer notes and dismiss them from dashboard"""
    customer = get_object_or_404(Customer, pk=customer_pk)
    
    # Handle DISMISS requests (from dashboard only)
    if request.method == 'POST' and 'note_id' in request.POST:
        note_id = request.POST.get('note_id')
        try:
            note = CustomerNote.objects.get(pk=note_id, customer=customer)
            # Mark as dismissed from dashboard instead of deleting
            note.is_dismissed_from_dashboard = True
            note.save()
            return JsonResponse({'success': True, 'message': 'নোট সফলভাবে মুছে ফেলা হয়েছে'})
        except CustomerNote.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'নোট পাওয়া যায়নি'}, status=404)
    
    # Handle GET requests
    try:
        # Get all notes (including dismissed ones) for customer profile
        notes = customer.notes.all()[:20]  # Get last 20 notes
        
        notes_data = []
        for note in notes:
            notes_data.append({
                'note': note.note,
                'created_at': note.created_at.strftime('%d/%m/%Y %H:%M'),
                'created_by': note.created_by.username if note.created_by else 'System'
            })
        
        return JsonResponse({'notes': notes_data})
    except Exception as e:
        # If table doesn't exist yet (migration not run), return empty notes
        return JsonResponse({'notes': [], 'error': str(e)})


# ==================== Deprecated Views (Keep for backward compatibility) ====================

@login_required
def submission_create(request, customer_pk):
    """DEPRECATED - Use transaction_submission_create instead"""
    return redirect('transaction_submission_create', customer_pk=customer_pk)


@login_required
def submission_detail(request, pk):
    """DEPRECATED - Transaction submission detail"""
    submission = get_object_or_404(CustomerSubmission, pk=pk)
    items = submission.items.all()
    
    total_spent = sum(item.total_price for item in items)
    remaining = submission.submitted_amount - total_spent
    
    context = {
        'submission': submission,
        'items': items,
        'total_spent': total_spent,
        'remaining': remaining,
    }
    return render(request, 'transactions/submission_detail.html', context)


@login_required
def submission_add_item(request, submission_pk):
    """DEPRECATED - Add item to submission"""
    submission = get_object_or_404(CustomerSubmission, pk=submission_pk)
    
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
                
                item = CustomerItem.objects.create(
                    submission=submission,
                    product_name=product_name,
                    product_description=product_description,
                    quantity=quantity,
                    unit_price=unit_price,
                )
                
                messages.success(request, f'✅ {product_name} successfully added!')
                return redirect('submission_detail', pk=submission_pk)
            except Exception as e:
                messages.error(request, f'❌ Error: {str(e)}')
    
    context = {
        'submission': submission,
    }
    return render(request, 'transactions/submission_add_item.html', context)


@login_required
def submission_remove_item(request, item_pk):
    """DEPRECATED - Remove item from submission"""
    item = get_object_or_404(CustomerItem, pk=item_pk)
    submission = item.submission
    
    if request.method == 'POST':
        product_name = item.product_name
        item.delete()
        messages.success(request, f'✅ {product_name} successfully removed!')
    
    return redirect('submission_detail', pk=submission.pk)


@login_required
def transaction_update_status(request, pk):
    """Quick update of order status and delivery status"""
    transaction = get_object_or_404(Transaction, pk=pk)
    
    # Only allow updating purchase transactions
    if transaction.transaction_type != 'purchase':
        messages.error(request, '❌ শুধুমাত্র ক্রয় লেনদেনের স্ট্যাটাস আপডেট করা যায়!')
        return redirect('transactions:customer_detail', pk=transaction.customer.pk)
    
    if request.method == 'POST':
        # Get form data
        new_status = request.POST.get('status', transaction.status)
        new_delivery_status = request.POST.get('delivery_status', transaction.delivery_status)
        
        # Update transaction
        transaction.status = new_status
        transaction.delivery_status = new_delivery_status
        transaction.save()
        
        # Record history
        TransactionHistory.objects.create(
            transaction=transaction,
            action='edited',
            old_balance=transaction.balance_before,
            new_balance=transaction.balance_after,
            notes=f'Status updated: {transaction.get_status_display()} / {transaction.get_delivery_status_display()}',
            performed_by=request.user
        )
        
        messages.success(request, f'✅ স্ট্যাটাস আপডেট হয়েছে! লেনদেন #: {transaction.transaction_number}')
    
    return redirect('transactions:customer_detail', pk=transaction.customer.pk)


@login_required
def customer_note_create(request, customer_pk):
    """Add a note to customer"""
    customer = get_object_or_404(Customer, pk=customer_pk)
    
    if request.method == 'POST':
        form = CustomerNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.customer = customer
            note.created_by = request.user
            note.save()
            messages.success(request, '✅ নোট সফলভাবে যোগ করা হয়েছে!')
        else:
            messages.error(request, '❌ নোট যোগ করতে সমস্যা হয়েছে!')
    
    return redirect('transactions:customer_detail', pk=customer.pk)


@login_required
def transaction_delete(request, pk):
    """Delete transaction (submission or withdrawal) with automatic balance adjustment"""
    transaction = get_object_or_404(Transaction, pk=pk)
    
    # Only allow deleting submission and withdrawal transactions
    if transaction.transaction_type not in ['submission', 'withdrawal']:
        messages.error(request, '❌ শুধুমাত্র জমা এবং উত্তোলন লেনদেন মুছে ফেলা যায়!')
        return redirect('transactions:customer_detail', pk=transaction.customer.pk)
    
    # Don't allow deleting already reversed transactions
    if transaction.is_reversed:
        messages.error(request, '❌ বাতিলকৃত লেনদেন মুছে ফেলা যায় না!')
        return redirect('transactions:customer_detail', pk=transaction.customer.pk)
    
    # Don't allow deleting already deleted transactions
    if transaction.is_deleted:
        messages.error(request, '❌ এই লেনদেন ইতিমধ্যে মুছে ফেলা হয়েছে!')
        return redirect('transactions:customer_detail', pk=transaction.customer.pk)
    
    customer = transaction.customer
    
    if request.method == 'POST':
        old_balance = customer.current_balance
        transaction_number = transaction.transaction_number
        transaction_type = transaction.get_transaction_type_display()
        amount = transaction.amount
        
        # Record history before deletion
        TransactionHistory.objects.create(
            transaction=transaction,
            action='deleted',
            old_balance=old_balance,
            new_balance=None,  # Will be calculated after deletion
            notes=f'Transaction deleted: {transaction_type} - ৳{amount}',
            performed_by=request.user
        )
        
        # Soft delete the transaction
        transaction.is_deleted = True
        transaction.deleted_at = timezone.now()
        transaction.save()
        
        # Recalculate customer balance (this will automatically exclude deleted transactions)
        customer.recalculate_balance()
        customer.save()
        
        # Update the history record with new balance
        history = TransactionHistory.objects.filter(transaction=transaction).order_by('-created_at').first()
        if history:
            history.new_balance = customer.current_balance
            history.save()
        
        messages.success(request, f'✅ লেনদেন সফলভাবে মুছে ফেলা হয়েছে! {transaction_number} - ব্যালেন্স স্বয়ংক্রিয়ভাবে সমন্বয় করা হয়েছে!')
        return redirect('transactions:customer_detail', pk=customer.pk)
    
    context = {
        'transaction': transaction,
        'customer': customer,
    }
    return render(request, 'transactions/transaction_delete_confirm.html', context)


