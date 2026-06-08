# 🧪 টেস্ট কাস্টম অর্ডার সিস্টেম - প্রোডাকশন গ্রেড

## 📋 সিস্টেম ওভারভিউ

টেস্ট কাস্টম অর্ডার সিস্টেম একটি সম্পূর্ণ লেনদেন-ভিত্তিক (transaction-based) ব্যবসা ব্যবস্থাপনা সিস্টেম যা:
- **জমা (Submission)**: গ্রাহক অগ্রিম টাকা জমা দেন
- **ক্রয় (Purchase)**: জমা থেকে পণ্য ক্রয় করেন
- **উত্তোলন (Withdrawal)**: অতিরিক্ত জমা ফেরত নেন
- **বাতিল (Reversal)**: যেকোনো লেনদেন বাতিল করা যায়
- **সম্পূর্ণ অডিট ট্রেইল**: প্রতিটি পরিবর্তন ট্র্যাক করা হয়

---

## 🎯 মূল ফিচার

### ✅ 1. লেনদেন ব্যবস্থাপনা
- **অটো-জেনারেটেড লেনদেন নাম্বার**: TCO-2026-00001 ফরম্যাটে
- **ব্যালেন্স ট্র্যাকিং**: পূর্ববর্তী এবং নতুন ব্যালেন্স রেকর্ড
- **স্ট্যাফ ট্র্যাকিং**: কে লেনদেন তৈরি করেছে
- **নেগেটিভ ব্যালেন্স অনুমোদিত**: ওভারস্পেন্ডিং সাপোর্ট

### ✅ 2. ইনভেন্টরি ইন্টিগ্রেশন
- ক্রয়ের সময় স্টক স্বয়ংক্রিয়ভাবে কমে
- বাতিলের সময় স্টক পুনরুদ্ধার হয়
- স্টক হিস্টরি ট্র্যাকিং
- লো স্টক ওয়ার্নিং

### ✅ 3. ভাউচার সিস্টেম
- **জমা ভাউচার**: সবুজ থিম
- **ক্রয় ভাউচার**: নীল থিম, পণ্য বিবরণ সহ
- **উত্তোলন ভাউচার**: হলুদ থিম
- **বাতিল ভাউচার**: লাল থিম, মূল লেনদেন রেফারেন্স সহ
- **প্রিন্ট-রেডি**: সব ভাউচার A4 সাইজে প্রিন্ট করা যায়

### ✅ 4. রিপোর্ট & স্টেটমেন্ট
- **কাস্টমার স্টেটমেন্ট**: সম্পূর্ণ লেনদেন ইতিহাস
- **তারিখ ফিল্টারিং**: নির্দিষ্ট সময়ের ডেটা দেখুন
- **লেনদেন টাইপ ফিল্টারিং**: শুধু জমা/ক্রয়/উত্তোলন দেখুন
- **প্রিন্ট-রেডি স্টেটমেন্ট**: পেশাদার ফরম্যাট

### ✅ 5. রিভার্সাল/অডিট সিস্টেম
- **নিরাপদ বাতিলকরণ**: ডেটা মুছে না, বাতিল মার্ক করে
- **স্বয়ংক্রিয় স্টক পুনরুদ্ধার**: ক্রয় বাতিলে স্টক ফিরে আসে
- **রিভার্সাল লিংকিং**: কোন লেনদেন কোনটি বাতিল করেছে তা ট্র্যাক
- **কনফার্মেশন স্ক্রিন**: প্রভাব দেখে তারপর বাতিল

---

## 🗂️ ডেটাবেস স্ট্রাকচার

### TestCustomer (টেস্ট কাস্টমার)
```python
- name: নাম
- mobile_number: মোবাইল নম্বর (unique)
- address: ঠিকানা
- current_balance: বর্তমান ব্যালেন্স (Decimal)
- created_at, updated_at
```

**Properties:**
- `total_submitted`: মোট জমার পরিমাণ
- `total_purchased`: মোট ক্রয়ের পরিমাণ
- `total_withdrawn`: মোট উত্তোলনের পরিমাণ

### TestCustomerTransaction (টেস্ট লেনদেন)
```python
- transaction_number: লেনদেন নাম্বার (auto-generated, unique)
- customer: ForeignKey(TestCustomer)
- transaction_type: submission/purchase/withdrawal/reversal
- amount: পরিমাণ (Decimal)
- balance_before: পূর্ববর্তী ব্যালেন্স
- balance_after: নতুন ব্যালেন্স
- status: pending/completed/cancelled

# ক্রয়ের জন্য
- item_name: পণ্যের নাম
- item_description: বিবরণ
- item_quantity: পরিমাণ
- item_unit_price: একক মূল্য
- inventory_product: ForeignKey(InventoryProduct)

# অডিট ট্রেইল
- reverses_transaction: ForeignKey(self) - কোন লেনদেন বাতিল
- is_reversed: বাতিল হয়েছে কিনা
- created_by: ForeignKey(User) - কে তৈরি করেছে
- notes: নোট
- created_at, updated_at
```

---

## 🔗 URL পাথ

### কাস্টমার ম্যানেজমেন্ট
- `/admin-panel/test-customers/` - কাস্টমার লিস্ট
- `/admin-panel/test-customers/create/` - নতুন কাস্টমার
- `/admin-panel/test-customers/<pk>/` - কাস্টমার ডিটেইল
- `/admin-panel/test-customers/<pk>/edit/` - কাস্টমার এডিট
- `/admin-panel/test-customers/<pk>/delete/` - কাস্টমার ডিলিট

### লেনদেন ম্যানেজমেন্ট
- `/admin-panel/test-customers/<customer_pk>/submission/` - জমা
- `/admin-panel/test-customers/<customer_pk>/purchase/` - ক্রয়
- `/admin-panel/test-customers/<customer_pk>/withdrawal/` - উত্তোলন
- `/admin-panel/test-customers/<customer_pk>/transactions/` - সব লেনদেন
- `/admin-panel/test-customers/<customer_pk>/statement/` - স্টেটমেন্ট

### ভাউচার & অ্যাকশন
- `/admin-panel/test-transactions/<pk>/voucher/` - ভাউচার দেখুন
- `/admin-panel/test-transactions/<pk>/reverse/` - বাতিল করুন

---

## 📊 ইউজার ওয়ার্কফ্লো

### 1️⃣ নতুন কাস্টমার যোগ করা
1. "টেস্ট অর্ডার" মেনুতে যান
2. "➕ নতুন কাস্টমার" ক্লিক করুন
3. নাম, মোবাইল, ঠিকানা দিন
4. সেভ করুন

### 2️⃣ টাকা জমা নেওয়া
1. কাস্টমার প্রোফাইলে যান
2. "💰 জমা দিন" বাটন ক্লিক করুন
3. পরিমাণ এবং নোট লিখুন
4. জমা নিশ্চিত করুন
5. ভাউচার প্রিন্ট করুন

### 3️⃣ পণ্য বিক্রয়
1. কাস্টমার প্রোফাইলে যান
2. "🛒 ক্রয় করুন" বাটন ক্লিক করুন
3. ইনভেন্টরি থেকে পণ্য নির্বাচন করুন
4. পরিমাণ ও মূল্য দিন
5. ক্রয় নিশ্চিত করুন
6. ভাউচার প্রিন্ট করুন
- স্টক স্বয়ংক্রিয়ভাবে কমে যাবে

### 4️⃣ টাকা ফেরত (উত্তোলন)
1. কাস্টমার প্রোফাইলে যান
2. "💸 টাকা উত্তোলন" বাটন ক্লিক করুন
3. পরিমাণ এবং কারণ লিখুন
4. উত্তোলন নিশ্চিত করুন
5. ভাউচার প্রিন্ট করুন

### 5️⃣ ভুল সংশোধন (রিভার্সাল)
1. কাস্টমার প্রোফাইল বা লেনদেন লিস্টে যান
2. ভুল লেনদেনের পাশে "↩️" বাটন ক্লিক করুন
3. প্রভাব দেখুন (ব্যালেন্স, স্টক)
4. "হ্যাঁ, বাতিল করুন" ক্লিক করুন
- নতুন রিভার্সাল লেনদেন তৈরি হবে
- ক্রয় হলে স্টক ফিরে আসবে

### 6️⃣ স্টেটমেন্ট তৈরি
1. কাস্টমার প্রোফাইলে যান
2. "📄 স্টেটমেন্ট" বাটন ক্লিক করুন
3. প্রয়োজনে তারিখ ফিল্টার করুন
4. প্রিন্ট করুন

---

## 🎨 UI ডিজাইন হাইলাইট

### রঙের থিম
- **জমা (Submission)**: সবুজ (#28a745)
- **ক্রয় (Purchase)**: নীল (#007bff)
- **উত্তোলন (Withdrawal)**: হলুদ (#ffc107)
- **বাতিল (Reversal)**: লাল (#dc3545)
- **পজিটিভ ব্যালেন্স**: সবুজ
- **নেগেটিভ ব্যালেন্স**: লাল

### কার্ড ডিজাইন
- গ্রেডিয়েন্ট ব্যাকগ্রাউন্ড
- রেসপন্সিভ গ্রিড লেআউট
- আইকন-বেসড অ্যাকশন
- ব্যাজ সিস্টেম

### প্রিন্ট অপটিমাইজেশন
- A4 সাইজ লেআউট
- হেডার ও ফুটার
- বর্ডার ও স্পেসিং
- মোনোস্পেস ফন্ট লেনদেন নম্বরের জন্য

---

## 🔧 টেকনিক্যাল ডিটেইল

### ব্যালেন্স ক্যালকুলেশন
```python
# জমা
balance_after = balance_before + amount

# ক্রয় / উত্তোলন
balance_after = balance_before - amount

# রিভার্সাল
if original_type == 'submission':
    balance_after = balance_before - amount  # জমা বাতিল
else:
    balance_after = balance_before + amount  # ক্রয়/উত্তোলন বাতিল
```

### স্টক ম্যানেজমেন্ট
```python
# ক্রয়ের সময়
inventory_product.remove_stock(quantity)
StockHistory.create(operation='sale')

# বাতিলের সময়
inventory_product.add_stock(quantity)
StockHistory.create(operation='adjustment')
```

### ট্রানজেকশন নাম্বার জেনারেশন
```python
Format: TCO-{YEAR}-{SEQUENCE}
Example: TCO-2026-00001, TCO-2026-00002, ...
```

---

## 📁 ফাইল স্ট্রাকচার

### Models
- `shop/models.py` - TestCustomer, TestCustomerTransaction

### Forms
- `shop/forms.py` - TestCustomerForm, TestTransactionSubmissionForm, TestTransactionPurchaseForm, TestTransactionWithdrawalForm

### Views
- `shop/views.py` - সব ভিউ ফাংশন

### URLs
- `shop/urls.py` - সব URL পাথ

### Templates
```
shop/templates/admin_panel/
├── test_customer_list.html
├── test_customer_detail.html
├── test_customer_form.html
├── test_customer_delete.html
├── test_transaction_submission_form.html
├── test_transaction_purchase_form.html
├── test_transaction_withdrawal_form.html
├── test_transaction_voucher.html
├── test_transaction_list.html
├── test_transaction_reverse_confirm.html
└── test_customer_statement.html
```

### Migrations
- `shop/migrations/0022_add_test_transaction_model.py`

---

## ✅ চেকলিস্ট

### ফিচার সম্পন্ন:
- ✅ TestCustomerTransaction মডেল
- ✅ অটো-জেনারেটেড লেনদেন নাম্বার
- ✅ জমা সিস্টেম (ফর্ম + ভাউচার)
- ✅ ক্রয় সিস্টেম (ইনভেন্টরি ইন্টিগ্রেশন সহ)
- ✅ উত্তোলন সিস্টেম (ব্যালেন্স চেক সহ)
- ✅ রিভার্সাল সিস্টেম (স্টক রিস্টোরেশন সহ)
- ✅ ইউনিভার্সাল ভাউচার টেমপ্লেট
- ✅ কাস্টমার স্টেটমেন্ট
- ✅ লেনদেন লিস্ট (ফিল্টারিং সহ)
- ✅ ব্যালেন্স ট্র্যাকিং (before/after)
- ✅ স্ট্যাফ ট্র্যাকিং (created_by)
- ✅ নেগেটিভ ব্যালেন্স সাপোর্ট
- ✅ প্রিন্ট-রেডি ডিজাইন
- ✅ রেসপন্সিভ UI
- ✅ বাংলা ইন্টারফেস

### টেস্টিং প্রয়োজন:
- [ ] নতুন কাস্টমার তৈরি করুন
- [ ] জমা দিন এবং ভাউচার প্রিন্ট করুন
- [ ] পণ্য ক্রয় করুন এবং স্টক চেক করুন
- [ ] টাকা উত্তোলন করুন
- [ ] লেনদেন বাতিল করুন এবং স্টক চেক করুন
- [ ] স্টেটমেন্ট প্রিন্ট করুন
- [ ] নেগেটিভ ব্যালেন্স টেস্ট করুন
- [ ] ফিল্টারিং টেস্ট করুন

---

## 🚀 ডিপ্লয়মেন্ট নোট

### মাইগ্রেশন
```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

### প্রোডাকশন চেকলিস্ট
- ✅ সব মাইগ্রেশন রান করা হয়েছে
- ✅ স্ট্যাটিক ফাইল কালেক্ট করা হয়েছে
- ✅ পারমিশন সেটআপ করা হয়েছে
- ⚠️ ব্যাকআপ সিস্টেম সেটআপ করুন
- ⚠️ ডেটা মাইগ্রেশন (পুরাতন সিস্টেম থেকে)

---

## 📞 সাপোর্ট

কোন সমস্যা বা প্রশ্নের জন্য সিস্টেম অ্যাডমিনিস্ট্রেটরের সাথে যোগাযোগ করুন।

**শপ নম্বর**: +8801727555673

---

**তৈরি**: June 8, 2026  
**ভার্সন**: 1.0.0 (Production Grade)  
**স্ট্যাটাস**: ✅ Ready for Testing
