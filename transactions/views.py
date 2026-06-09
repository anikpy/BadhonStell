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
    """Transaction customer list"""
    search_query = request.GET.get('search', '')
    
    customers = Customer.objects.all().order_by('-created_at')
    
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
    
    # Get all transactions
    transactions = customer.transactions.filter(status='completed').order_by('-created_at')
    
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
        # Delete all transactions first (cascade will handle this, but being explicit)
        if has_transactions:
            customer.transactions.all().delete()
        customer.delete()
        
        if has_transactions:
            messages.warning(request, f'⚠️ {name} and {transaction_count} transactions successfully deleted!')
        else:
            messages.success(request, f'✅ {name} successfully deleted!')
        
        return redirect('customer_list')
    
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


# ==================== Transaction Management ====================

@login_required
def transaction_submission_create(request, customer_pk):
    """Transaction - create submission (deposit)"""
    customer = get_object_or_404(Customer, pk=customer_pk)
    
    if request.method == 'POST':
        form = TransactionSubmissionForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            notes = form.cleaned_data.get('notes', '')
            
            # Create transaction
            transaction = Transaction.objects.create(
                customer=customer,
                transaction_type='submission',
                amount=amount,
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
                
                # Create main transaction
                item_names = ', '.join([item['product_name'] for item in validated_items])
                transaction = Transaction.objects.create(
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
                
                messages.success(request, f'✅ Purchase successful! ৳{final_total} | Transaction #: {transaction.transaction_number}')
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
            notes = form.cleaned_data.get('notes', '')
            
            # Create transaction (amount is negative for withdrawal)
            transaction = Transaction.objects.create(
                customer=customer,
                transaction_type='withdrawal',
                amount=amount,
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
    
    context = {
        'transaction': transaction,
        'customer': transaction.customer,
    }
    return render(request, 'transactions/transaction_voucher.html', context)


@login_required
def transaction_list(request, customer_pk):
    """Transaction list - for specific customer"""
    customer = get_object_or_404(Customer, pk=customer_pk)
    
    transaction_type = request.GET.get('type', '')
    date_from = request.GET.get('from_date', '')
    date_to = request.GET.get('to_date', '')
    
    transactions = customer.transactions.filter(status='completed').order_by('-created_at')
    
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
    """Reverse/cancel transaction"""
    transaction = get_object_or_404(Transaction, pk=pk)
    
    if transaction.is_reversed:
        messages.error(request, '❌ This transaction has already been reversed!')
        return redirect('transactions:customer_detail', pk=transaction.customer.pk)
    
    if request.method == 'POST':
        # Store old balance for history
        old_balance = transaction.customer.current_balance
        
        # Create reversal transaction
        reversal_amount = -transaction.amount if transaction.transaction_type == 'submission' else transaction.amount
        
        reversal = Transaction.objects.create(
            customer=transaction.customer,
            transaction_type='reversal',
            amount=reversal_amount,
            notes=f'Reversal: {transaction.transaction_number} - {transaction.get_transaction_type_display()}',
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
                        notes=f'Transaction reversal: {transaction.transaction_number}'
                    )
        
        # Record history for both original and reversal
        TransactionHistory.objects.create(
            transaction=transaction,
            action='reversed',
            old_balance=old_balance,
            new_balance=transaction.customer.current_balance,
            notes=f'Transaction reversed: {transaction.transaction_number}',
            performed_by=request.user
        )
        
        TransactionHistory.objects.create(
            transaction=reversal,
            action='created',
            old_balance=old_balance,
            new_balance=reversal.balance_after,
            notes=f'Reversal created: {transaction.transaction_number}',
            performed_by=request.user
        )
        
        messages.success(request, f'✅ Transaction reversal successful! Reversal #: {reversal.transaction_number}')
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
    transactions = customer.transactions.filter(status='completed').order_by('order_date')
    
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
def customer_notes_api(request, customer_pk):
    """API endpoint to get customer notes"""
    customer = get_object_or_404(Customer, pk=customer_pk)
    
    try:
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


