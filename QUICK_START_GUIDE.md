# 🚀 QUICK START GUIDE - Test Custom Order System

## ⚡ 30-Second Setup

1. **System is ready to use!** No additional setup needed.
2. Navigate to: `http://localhost:8000/admin-panel/`
3. Click on **"🧪 টেস্ট অর্ডার"** in navbar

---

## 📝 5-Minute Tutorial

### Step 1: Create a Test Customer (2 min)
1. Click **"➕ নতুন কাস্টমার"** button
2. Fill in:
   - **নাম**: "রহিম আহমেদ"
   - **মোবাইল**: "01712345678"
   - **ঠিকানা**: "Kendua, Netrokona"
3. Click **"সংরক্ষণ করুন"**

### Step 2: Add Deposit/Submission (1 min)
1. Click on customer profile
2. Click **"💰 জমা দিন"** (green button)
3. Enter amount: **10000**
4. Click **"জমা নিশ্চিত করুন"**
5. **Print voucher** if needed

### Step 3: Make Purchase (1 min)
1. Back to customer profile
2. Click **"🛒 ক্রয় করুন"** (blue button)
3. Select a product from inventory
4. Enter quantity and price
5. Click **"ক্রয় নিশ্চিত করুন"**
6. Check that balance updated and inventory stock decreased

### Step 4: Withdrawal (1 min)
1. Back to customer profile
2. Click **"💸 টাকা উত্তোলন"** (yellow button)
3. Enter amount: **2000**
4. Click **"উত্তোলন নিশ্চিত করুন"**
5. Balance should now be: 10000 - 3000 (purchase) - 2000 (withdrawal) = **5000**

---

## 🔄 Key Features to Test

### ✅ Feature 1: Voucher Printing
- On any transaction, click the **🧾 icon**
- Click **"🖨️ প্রিন্ট করুন"** button
- Voucher should print in A4 format

### ✅ Feature 2: Transaction History
- Click **"📋 সব লেনদেন"** button
- All transactions show with:
  - Transaction number (TCO-2026-XXXXX)
  - Type (জমা/ক্রয়/উত্তোলন)
  - Amount and balance changes
- Click **🧾** to see voucher
- Click **↩️** to reverse

### ✅ Feature 3: Statement/Report
- Click **"📄 স্টেটমেন্ট"** button
- See complete transaction history
- Click **"🖨️ প্রিন্ট করুন"** to print statement

### ✅ Feature 4: Reversals (Undo)
1. Go to any transaction
2. Click **↩️ (undo/reverse)** icon
3. Review impact on balance
4. Click **"হ্যাঁ, বাতিল করুন"** to confirm
5. If it was a purchase, inventory stock is restored!

### ✅ Feature 5: Negative Balance
1. Create customer, add ৳5000 submission
2. Purchase ৳8000 worth of products
3. Balance becomes: -৳3000 (negative)
4. This is allowed! Customer owes money

---

## 📊 Live Data Example

```
Customer: রহিম আহমেদ
Mobile: 01712345678

Transactions:
1. ত্মা (জমা) - +10000 → Balance: 10000
2. ক্রয় (ক্রয়) - -3000  → Balance: 7000
3. উত্তোলন - -2000  → Balance: 5000
```

---

## 🎨 UI Color Guide

| Color | Type | Meaning |
|-------|------|---------|
| 🟢 Green | জমা | Customer deposits money |
| 🔵 Blue | ক্রয় | Purchase from inventory |
| 🟡 Yellow | উত্তোলন | Withdraw cash refund |
| 🔴 Red | বাতিল | Reversal/Undo transaction |

---

## 💡 Pro Tips

### Tip 1: Generate Custom Numbers
- Each transaction auto-gets unique number
- Format: TCO-2026-00001, TCO-2026-00002, etc.
- Easy to track and reference

### Tip 2: Print Everything
- All vouchers and statements are print-ready
- Click **"🖨️ প্রিন্ট করুন"** to print
- Perfect for A4 paper

### Tip 3: Undo Any Mistake
- Made a wrong entry? No problem!
- Click **↩️** on any transaction
- It creates a reversal transaction (doesn't delete)
- Balance and stock automatically corrected

### Tip 4: Filter Transactions
- View → "সব লেনদেন" (All Transactions)
- Filter by type or date range
- Find specific transactions quickly

### Tip 5: Track Everything
- Every change is recorded
- See who created each transaction
- Balance before/after tracked
- Complete audit trail

---

## ❌ Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "স্টক অপর্যাপ্ত" | That product doesn't have enough stock in inventory |
| "এই মোবাইল ইতিমধ্যে আছে" | Customer already exists, edit instead of create |
| Negative balance | This is allowed! Customer can owe money |
| "কোনো লেনদেন নেই" | Customer hasn't made any transactions yet |

---

## 📱 Navigation Map

```
Main Menu
├── 🧪 টেস্ট অর্ডার (Test Orders)
│   ├── Customer List
│   │   ├── View Customer Profile
│   │   │   ├── 💰 জমা দিন (Add Submission)
│   │   │   ├── 🛒 ক্রয় করুন (Add Purchase)
│   │   │   ├── 💸 টাকা উত্তোলন (Add Withdrawal)
│   │   │   ├── 📋 সব লেনদেন (View Transactions)
│   │   │   └── 📄 স্টেটমেন্ট (Print Statement)
│   │   ├── ➕ নতুন কাস্টমার (New Customer)
│   │   ├── ✏️ এডিট (Edit)
│   │   └── 🗑️ মুছুন (Delete)
│   └── Transactions
│       ├── 🧾 ভাউচার (View Voucher)
│       └── ↩️ বাতিল (Reverse)
```

---

## 🎯 Common Workflows

### Workflow 1: Simple Purchase
```
1. Create Customer
2. Add Submission (জমা)
3. Add Purchase (ক্রয়)
4. View Voucher
5. Print Statement
```

### Workflow 2: Refund After Mistake
```
1. Go to customer profile
2. Click "📋 সব লেনদেন"
3. Find wrong transaction
4. Click "↩️" to reverse
5. Confirm reversal
6. Balance & stock auto-corrected!
```

### Workflow 3: Track Customer
```
1. Go to customer profile
2. See "বর্তমান ব্যালেন্স" (current balance)
3. See "মোট জমা" (total submitted)
4. See "মোট ক্রয়" (total purchased)
5. Click "📄 স্টেটমেন্ট" for full history
```

---

## 📞 Emergency Contacts

**Issues?**
- Read: `TEST_CUSTOM_ORDER_DOCUMENTATION.md`
- Check: `SYSTEM_TEST_REPORT.md`
- Contact: Admin

**Server Down?**
```bash
python3 manage.py runserver
```

---

## 🎓 Learning Resources

1. **Full Documentation**: `TEST_CUSTOM_ORDER_DOCUMENTATION.md`
2. **System Report**: `SYSTEM_TEST_REPORT.md`
3. **Code Location**: `shop/models.py`, `shop/views.py`, `shop/forms.py`
4. **Templates**: `shop/templates/admin_panel/test_*.html`

---

## ✅ Ready to Go!

```
✅ All systems operational
✅ Database ready
✅ Models working
✅ Views tested
✅ Templates rendering
✅ Ready for production

🚀 Start creating transactions now!
```

---

**Last Updated**: June 8, 2026  
**System Status**: ✅ LIVE  
**Support**: Available 24/7
