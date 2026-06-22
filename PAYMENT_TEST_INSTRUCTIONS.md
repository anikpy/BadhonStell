# পেমেন্ট সিস্টেম টেস্টিং নির্দেশিকা

## টেস্ট কাস্টমার
- **নাম:** Md Arifur Rahman Anik
- **মোবাইল:** 01627220071
- **Customer ID:** 73
- **Current Balance:** -৳100.00 (বাকি)

## টেস্ট URL
http://127.0.0.1:8000/admin-panel/transactions/customers/73/purchase/create/

---

## টেস্ট কেস ১: সম্পূর্ণ পরিশোধ (Exact Payment)

### Steps:
1. পণ্য যোগ করুন: নাম="Test Product 1", পরিমাণ=10, মূল্য=100
2. মোট দেখাবে: **৳1000**
3. "গ্রাহক টাকা দিয়েছেন" চেক করুন
4. টাকার পরিমাণ: **৳1000** (auto-filled হবে)
5. স্ট্যাটাস দেখাবে: ✅ সম্পূর্ণ পরিশোধ
6. Submit করুন

### Expected Result:
- ✅ Purchase transaction তৈরি: -৳1000
- ✅ Submission transaction তৈরি: +৳1000
- ✅ Net balance change: ৳0
- ✅ Final balance: -৳1100 (আগের -৳100 থেকে)
- ✅ Message: "সম্পূর্ণ পরিশোধ: ৳1000"

### Verify:
```
Statement page: দুটো transaction দেখাবে
- Purchase: -৳1000
- Submission: +৳1000 (পেমেন্ট (ক্রয় থেকে))
```

---

## টেস্ট কেস ২: আংশিক পরিশোধ (Partial Payment)

### Steps:
1. পণ্য যোগ করুন: নাম="Test Product 2", পরিমাণ=5, মূল্য=200
2. মোট দেখাবে: **৳1000**
3. "গ্রাহক টাকা দিয়েছেন" চেক করুন
4. টাকার পরিমাণ: **৳400** (1000 এর চেয়ে কম)
5. স্ট্যাটাস দেখাবে: ⚠️ আংশিক পরিশোধ | বাকি: ৳600
6. Submit করুন

### Expected Result:
- ✅ Purchase transaction তৈরি: -৳1000
- ✅ Submission transaction তৈরি: +৳400
- ✅ Net balance change: -৳600 (বাকি)
- ✅ Message: "আংশিক পরিশোধ: ৳400, বাকি: ৳600"

### Verify:
```
Statement page:
- Purchase: -৳1000
- Submission: +৳400 (আংশিক পেমেন্ট (ক্রয় থেকে))
- Net effect: -৳600 added to balance
```

---

## টেস্ট কেস ৩: অতিরিক্ত জমা (Overpayment)

### Steps:
1. পণ্য যোগ করুন: নাম="Test Product 3", পরিমাণ=2, মূল্য=500
2. মোট দেখাবে: **৳1000**
3. "গ্রাহক টাকা দিয়েছেন" চেক করুন
4. টাকার পরিমাণ: **৳1500** (1000 এর চেয়ে বেশি)
5. স্ট্যাটাস দেখাবে: 💰 অতিরিক্ত জমা | অতিরিক্ত: ৳500
6. Submit করুন

### Expected Result:
- ✅ Purchase transaction তৈরি: -৳1000
- ✅ Submission transaction তৈরি: +৳1500
- ✅ Net balance change: +৳500 (advance)
- ✅ Message: "পরিশোধ: ৳1500 (অতিরিক্ত জমা: ৳500)"

### Verify:
```
Statement page:
- Purchase: -৳1000
- Submission: +৳1500 (পেমেন্ট (ক্রয় থেকে))
- Net effect: +৳500 added to balance (advance)
```

---

## টেস্ট কেস ৪: পেমেন্ট ছাড়া (No Payment)

### Steps:
1. পণ্য যোগ করুন: নাম="Test Product 4", পরিমাণ=3, মূল্য=100
2. মোট দেখাবে: **৳300**
3. "গ্রাহক টাকা দিয়েছেন" চেক করবেন না (unchecked রাখুন)
4. Submit করুন

### Expected Result:
- ✅ শুধু Purchase transaction তৈরি: -৳300
- ✅ কোন Submission transaction নেই
- ✅ Net balance change: -৳300 (সম্পূর্ণ বাকি)
- ✅ Message: "Purchase successful!" (কোন payment message নেই)

### Verify:
```
Statement page:
- Purchase: -৳300 (একটা মাত্র transaction)
```

---

## টেস্ট কেস ৫: মাল্টিপল আইটেম + ডিসকাউন্ট + পেমেন্ট

### Steps:
1. আইটেম ১: নাম="Product A", পরিমাণ=5, মূল্য=100, ছাড়=10%
   - Net: ৳450
2. আইটেম ২: নাম="Product B", পরিমাণ=3, মূল্য=200, ছাড়=5%
   - Net: ৳570
3. Subtotal: ৳1020
4. মোট ছাড়: 5% দিন
5. Final Total: **৳969**
6. "গ্রাহক টাকা দিয়েছেন" চেক করুন
7. টাকার পরিমাণ: **৳1000**
8. স্ট্যাটাস: অতিরিক্ত জমা ৳31
9. Submit করুন

### Expected Result:
- ✅ Purchase: -৳969 (2 items with discount)
- ✅ Submission: +৳1000
- ✅ Net: +৳31 (advance)

---

## চেক লিস্ট

### Frontend (UI):
- [ ] পেমেন্ট সেকশন পণ্য যোগ করার পরে দেখা যাচ্ছে
- [ ] Checkbox toggle করলে amount field দেখা যাচ্ছে
- [ ] Auto-fill total amount দিয়ে হচ্ছে
- [ ] Payment status real-time update হচ্ছে
- [ ] তিনটা status ঠিকমতো দেখাচ্ছে (exact, partial, overpayment)

### Backend (Logic):
- [ ] Exact payment: Purchase + Submission তৈরি হচ্ছে, net = 0
- [ ] Partial payment: Purchase + Submission তৈরি হচ্ছে, net = negative
- [ ] Overpayment: Purchase + Submission তৈরি হচ্ছে, net = positive
- [ ] No payment: শুধু Purchase তৈরি হচ্ছে

### Statement Page:
- [ ] সব transactions দেখা যাচ্ছে
- [ ] Purchase এবং Submission আলাদা আলাদা line item
- [ ] Running balance সঠিক হচ্ছে
- [ ] Notes field এ reference দেখা যাচ্ছে

### Voucher Page:
- [ ] Purchase voucher ঠিকমতো দেখাচ্ছে
- [ ] সব products এবং prices সঠিক
- [ ] Discount সঠিক calculate হচ্ছে

---

## ক্লিনআপ কমান্ড

টেস্টিং শেষে test data মুছতে:

```bash
cd /home/anik/GitProject/BadhonStell
venv/bin/python3 manage.py shell
```

```python
from transactions.models import Customer, Transaction
customer = Customer.objects.get(pk=73)

# Delete test transactions
customer.transactions.filter(notes__icontains='Test').delete()
# OR delete by transaction number pattern
customer.transactions.filter(item_name__icontains='Test').delete()

# Recalculate balance
customer.current_balance = customer.recalculate_balance()
customer.save()
```

---

## সমস্যা হলে চেক করুন:

1. **Browser cache**: Hard refresh (Ctrl+Shift+R)
2. **Django server**: Restart করুন
3. **JavaScript errors**: Browser console (F12) চেক করুন
4. **Database**: Statement page দেখে transactions verify করুন
