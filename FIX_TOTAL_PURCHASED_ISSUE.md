# Fix: মোট ক্রয় (Total Purchase) Showing ৳0 in Customer Statement

## Problem

Customer 78's statement at `http://127.0.0.1:8000/admin-panel/transactions/customers/78/statement/` was showing:
- **মোট ক্রয় ৳0** (Total Purchase ৳0) - **WRONG**

The customer actually had a purchase of **৳80,200** which was not showing up.

## Root Cause

The issue was in the `Customer.total_purchased` property in `/home/anik/GitProject/BadhonStell/transactions/models.py` (lines 37-54).

### Original Code (BUGGY)
```python
@property
def total_purchased(self):
    """Total purchases (ক্রয়) - only ACTIVE orders"""
    purchases = self.transactions.filter(
        transaction_type='purchase',
        is_reversed=False,
        is_deleted=False
    ).exclude(
        status='cancelled'
    )
    
    # BUG: Was summing due_amount instead of amount
    total_due = 0
    for purchase in purchases:
        due_amount = purchase.due_amount if hasattr(purchase, 'due_amount') else purchase.amount
        total_due += due_amount
    
    return abs(total_due)
```

### The Problem
The code was summing `due_amount` (which represents remaining balance after cash payment) instead of `amount` (which represents total purchase value).

For customer 78:
- Purchase amount: ৳80,200
- Cash paid: ৳0
- Due amount: ৳0 (was incorrectly set)
- Result: Total purchased showed ৳0 instead of ৳80,200

## Fix Applied

### 1. Fixed the `total_purchased` property

**File:** `/home/anik/GitProject/BadhonStell/transactions/models.py`

```python
@property
def total_purchased(self):
    """Total purchases (ক্রয়) - only ACTIVE orders"""
    from django.db.models import Sum
    purchases = self.transactions.filter(
        transaction_type='purchase',
        is_reversed=False,
        is_deleted=False
    ).exclude(
        status='cancelled'
    )
    
    # FIXED: Now sums the full purchase amount
    total_amount = purchases.aggregate(total=Sum('amount'))['total'] or 0
    return abs(total_amount)
```

### 2. Fixed all purchase transactions' `due_amount` field

Many purchase transactions had `due_amount = 0` when it should be `amount - cash_paid`.

**Created script:** `fix_all_due_amounts.py`

This script:
- Fixed 65 out of 66 purchase transactions
- Updated `due_amount = amount - cash_paid` for all purchases
- Recalculated customer balances

## Verification

After the fix, customer 78's statement now correctly shows:

```
মোট জমা (Total Submitted): ৳31,000
মোট ক্রয় (Total Purchased): ৳80,200  ✓ FIXED
মোট উত্তোলন (Total Withdrawn): ৳0
চূড়ান্ত ব্যালেন্স (Final Balance): ৳-49,200
```

The customer owes ৳49,200 to the shop (বাকি).

## Important Notes

### Difference between `amount` and `due_amount`

- **`amount`**: Total purchase value (used for "মোট ক্রয়" display)
- **`due_amount`**: Remaining balance after cash payment (used for balance calculation)
- **`cash_paid`**: Cash paid at purchase time

**Formula:** `due_amount = amount - cash_paid`

### Where each is used

1. **Display "মোট ক্রয়" (Total Purchase)**: Use `amount` - shows total value of purchases
2. **Calculate balance**: Use `due_amount` - shows what customer still owes
3. **Statement balance**: `total_submitted - total_due - total_withdrawn`

## Files Modified

1. `/home/anik/GitProject/BadhonStell/transactions/models.py` - Fixed `total_purchased` property
2. Created `fix_all_due_amounts.py` - One-time data fix script
3. Created `fix_customer_78_due_amount.py` - Specific fix for customer 78

## Testing

To verify the fix works:

```bash
cd /home/anik/GitProject/BadhonStell
source venv/bin/activate
python manage.py runserver
```

Then visit: `http://127.0.0.1:8000/admin-panel/transactions/customers/78/statement/`

You should now see **মোট ক্রয় ৳80,200** correctly displayed.

## Status

✅ **FIXED** - The issue has been resolved and tested.
