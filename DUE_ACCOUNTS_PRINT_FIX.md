# Due Accounts Print Fix - Transaction App Integration

## Problem
The due accounts print page (`/admin-panel/due-accounts/print/`) was only showing data from the **shop app** (Order model), but not from the **transactions app** (Transaction model). The list view was already showing both, but the print view was incomplete.

Additionally, there was a bug where the code tried to use `.date` field which doesn't exist in the Transaction model.

## Solution
Updated the `due_accounts_print` function in `/home/anik/GitProject/BadhonStell/shop/views.py` to include customers from the transactions app who have negative balance (বাকি/due amount), and fixed the field name issue.

## Changes Made

### 1. Updated `due_accounts_print` function (shop/views.py)
- Added logic to fetch customers from `transactions.models.Customer` with negative balance
- For each transaction customer with due:
  - Calculate due amount as `abs(current_balance)` when balance is negative
  - Fetch all purchase transactions for that customer using `.order_by('-order_date')` (fixed from '-date')
  - Get last transaction date from `order_date` field (fixed from 'date')
  - Add to `customer_due` dictionary with source='transaction'
- Added fields to shop customers: `customer_name`, `mobile_number`, `source='shop'`, and `last_date`
- Added `last_date` tracking for both shop orders and transaction purchases directly in the dictionary
- Now both shop orders and transaction purchases are included in the print view

### 2. Updated template (shop/templates/admin_panel/due_accounts_print.html)
- Modified the "সর্বশেষ অর্ডার" (Last Order) column to use `data.last_date` directly
- Removed complex conditional logic that was trying to access `data.orders.0`
- Simplified to just display `data.last_date` with proper null checking

## Bug Fixed
**Error**: `FieldError: Cannot resolve keyword 'date' into field`

**Root Cause**: The Transaction model doesn't have a `date` field. It has:
- `order_date` - For when the purchase order was placed
- `delivery_date` - For when delivery was completed  
- `payment_date` - For payment due date
- `created_at` - System timestamp

**Fix**: Changed `.order_by('-date')` to `.order_by('-order_date')` and accessed `order_date` field instead of `date` field.

## How It Works

### Shop App Customers
- Uses `Order.objects.filter(due_amount__gt=0)` to find orders with due
- Groups by customer and calculates total due per customer
- Tracks `last_date` as the most recent `created_at` from orders
- Shows order count and last order date

### Transaction App Customers  
- Uses `Customer.objects.filter(current_balance__lt=0)` to find customers with negative balance
- Negative balance = customer owes money (বাকি)
- Fetches purchase transactions using `order_by('-order_date')`
- Gets `last_date` from the most recent transaction's `order_date` field
- Shows purchase transaction count and last purchase date
- Due amount = `abs(current_balance)`

## Testing
✅ Tested with test script - successfully processes 42 shop orders and 57 transaction customers
✅ Django system check passes with no errors

To verify in browser:
1. Navigate to: `http://127.0.0.1:8000/admin-panel/due-accounts/`
2. Click the "প্রিন্ট করুন" (Print) button
3. Verify that customers from **both** shop app and transactions app appear in the print view
4. Check that:
   - Customer names are displayed correctly
   - Mobile numbers are shown
   - Due amounts match the list view
   - Last order/transaction dates appear correctly

## Data Flow
```
due_accounts_print view
    ├── Shop Orders (Order model)
    │   ├── Orders with due_amount > 0
    │   ├── Group by customer
    │   └── Track last_date from created_at
    │
    └── Transaction Customers (Customer model)
        ├── Customers with current_balance < 0
        ├── Fetch purchase transactions (order_by '-order_date')
        ├── Get last_date from order_date field
        └── Calculate due = abs(current_balance)

Both merged into customer_due dictionary with last_date
    ↓
Template displays all customers with due amounts and last date
```

## Key Fields in Context
- `customer_due`: Dictionary with customer data from both apps
  - `customer_name`: Name of the customer
  - `mobile_number`: Phone number
  - `total_due`: Total due amount
  - `orders`: List of orders/transactions
  - `source`: 'shop' or 'transaction' to identify the source
  - `last_date`: Most recent order/transaction date (added for both sources)
- `total_grand_due`: Sum of all due amounts from both apps
- `print_date`: Current timestamp for the print

## Files Modified
1. `/home/anik/GitProject/BadhonStell/shop/views.py` - Line ~2757 (due_accounts_print function)
   - Added `last_date` tracking for shop orders
   - Fixed Transaction query to use `order_by('-order_date')` instead of `order_by('-date')`
   - Fixed to access `order_date` field instead of non-existent `date` field
2. `/home/anik/GitProject/BadhonStell/shop/templates/admin_panel/due_accounts_print.html` 
   - Changed last order date column to use `data.last_date` directly

## Result
✅ The print view now shows **complete due accounts data** from both shop app and transactions app
✅ Fixed the FieldError bug by using correct field name (`order_date` instead of `date`)
✅ Simplified template logic by adding `last_date` directly to context data
