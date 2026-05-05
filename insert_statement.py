#!/usr/bin/env python3
"""Insert customer_statement view into shop/views.py"""

import sys

# Read the original file
with open('shop/views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line after customer_delete function
insert_position = None
for i, line in enumerate(lines):
    if 'def customer_delete(request, pk):' in line:
        # Find the end of this function (next @login_required or end of file)
        for j in range(i+1, len(lines)):
            if lines[j].strip().startswith('@login_required') or lines[j].strip().startswith('def ') and not lines[j].strip().startswith('def customer_delete'):
                insert_position = j
                break
        if insert_position is None:
            insert_position = len(lines)
        break

if insert_position is None:
    print("ERROR: Could not find insertion point")
    sys.exit(1)

# Create the new function
new_function = '''@login_required
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

'''

# Insert the new function
lines.insert(insert_position, new_function)

# Write back
with open('shop/views.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"✅ customer_statement function inserted at line {insert_position+1}")