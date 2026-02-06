# বাধন স্টিল - ওয়েব অ্যাপ্লিকেশন

একটি সম্পূর্ণ Django ভিত্তিক ওয়েব অ্যাপ্লিকেশন স্টিল ও লোহার দোকানের জন্য।

## ফিচারসমূহ

### কাস্টমার সাইট
- হোম পেজে দোকানের তথ্য ও পণ্য প্রদর্শন
- পণ্য তালিকা পেজ (ক্যাটাগরি অনুযায়ী ফিল্টার)
- পণ্যের বিস্তারিত তথ্য (নাম, ছবি, বিবরণ, দাম)
- সরাসরি ফোন ও হোয়াটসঅ্যাপে যোগাযোগ

### কাস্টম অ্যাডমিন প্যানেল
- সুরক্ষিত লগইন সিস্টেম
- ড্যাশবোর্ড (পরিসংখ্যান সহ)
- অর্ডার ম্যানেজমেন্ট (তৈরি, সম্পাদনা, মুছে ফেলা)
- সার্চ ফিচার (নাম, মোবাইল, পণ্য অনুযায়ী)
- অর্ডার স্ট্যাটাস ম্যানেজমেন্ট (চলমান/সম্পন্ন)
- প্রিন্টযোগ্য ভাউচার/ইনভয়েস

### অন্যান্য ফিচার
- সম্পূর্ণ বাংলা ইন্টারফেস
- Responsive Design (মোবাইল ও কম্পিউটার সাপোর্ট)
- বাকি টাকা অটো ক্যালকুলেশন
- সুন্দর UI/UX ডিজাইন

## প্রযুক্তি

- **Backend:** Django 4.2+
- **Database:** SQLite (ডিফল্ট)
- **Frontend:** HTML, CSS (বাংলা ফন্ট সাপোর্ট)
- **Image Handling:** Pillow

## ইনস্টলেশন গাইড

### ১. প্রয়োজনীয় সফটওয়্যার
- Python 3.8 বা তার উপরের ভার্সন
- pip (Python package manager)

### ২. প্রোজেক্ট সেটআপ

```bash
# Virtual environment তৈরি করুন (যদি না থাকে)
python -m venv venv

# Virtual environment সক্রিয় করুন
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# প্রয়োজনীয় প্যাকেজ ইনস্টল করুন
pip install -r requirements.txt
```

### ৩. ডাটাবেস সেটআপ

```bash
# Database migrations তৈরি করুন
python manage.py makemigrations

# Migrations প্রয়োগ করুন
python manage.py migrate
```

### ৪. অ্যাডমিন ইউজার তৈরি

```bash
# Superuser তৈরি করুন
python manage.py createsuperuser

# Username, Email, Password দিন
# উদাহরণ:
# Username: admin
# Email: admin@badhonsteel.com
# Password: (আপনার পছন্দের পাসওয়ার্ড)
```

### ৫. দোকানের তথ্য যোগ করুন

```bash
# Django shell খুলুন
python manage.py shell
```

```python
# Shell এ নিচের কোড রান করুন
from shop.models import ShopInfo

shop = ShopInfo.objects.create(
    name='বাধন স্টিল',
    description='স্টিল ও লোহার সকল ধরনের কাজ করা হয়। দরজা, জানালা, গ্রিল, গেট, রেলিং, শেড ইত্যাদি।',
    phone='01XXXXXXXXX',
    whatsapp='01XXXXXXXXX',
    address='আপনার দোকানের ঠিকানা'
)

print("দোকানের তথ্য যোগ হয়েছে!")
exit()
```

### ৬. সার্ভার চালু করুন

```bash
# Development server চালু করুন
python manage.py runserver

# ব্রাউজারে খুলুন: http://127.0.0.1:8000/
```

## ব্যবহার নির্দেশিকা

### কাস্টমার সাইট
- **হোম পেজ:** http://127.0.0.1:8000/
- **পণ্য তালিকা:** http://127.0.0.1:8000/products/

### অ্যাডমিন প্যানেল
- **লগইন:** http://127.0.0.1:8000/admin-panel/login/
- **ড্যাশবোর্ড:** http://127.0.0.1:8000/admin-panel/
- **অর্ডার তালিকা:** http://127.0.0.1:8000/admin-panel/orders/
- **নতুন অর্ডার:** http://127.0.0.1:8000/admin-panel/orders/create/

### Django Admin (ডাটা ম্যানেজমেন্ট)
- **URL:** http://127.0.0.1:8000/django-admin/
- এখানে পণ্য, দোকানের তথ্য ইত্যাদি যোগ/সম্পাদনা করতে পারবেন

## পণ্য যোগ করার পদ্ধতি

১. Django Admin এ লগইন করুন: http://127.0.0.1:8000/django-admin/
২. "পণ্যসমূহ" সেকশনে যান
৩. "পণ্য যোগ করুন" ক্লিক করুন
৪. পণ্যের তথ্য পূরণ করুন:
   - পণ্যের নাম
   - ক্যাটাগরি নির্বাচন করুন
   - ছবি আপলোড করুন
   - বিবরণ লিখুন
   - আনুমানিক দাম দিন
৫. "সংরক্ষণ করুন" ক্লিক করুন

## অর্ডার ম্যানেজমেন্ট

### নতুন অর্ডার তৈরি
১. অ্যাডমিন প্যানেলে লগইন করুন
২. "নতুন অর্ডার" বাটনে ক্লিক করুন
৩. ফর্ম পূরণ করুন:
   - ক্রেতার নাম
   - মোবাইল নাম্বার
   - পণ্যের নাম ও বিবরণ
   - মোট মূল্য
   - নগদ পরিশোধ (বাকি টাকা অটো হিসাব হবে)
   - অর্ডার ও ডেলিভারির তারিখ
৪. "অর্ডার তৈরি করুন" ক্লিক করুন

### ভাউচার প্রিন্ট
১. অর্ডার তালিকা থেকে "ভাউচার" বাটনে ক্লিক করুন
২. নতুন ট্যাবে ভাউচার খুলবে
৩. "প্রিন্ট করুন" বাটনে ক্লিক করুন

## ডাটাবেস স্ট্রাকচার

### ShopInfo (দোকানের তথ্য)
- name: দোকানের নাম
- logo: লোগো (ছবি)
- description: বিবরণ
- phone: ফোন নাম্বার
- whatsapp: হোয়াটসঅ্যাপ নাম্বার
- address: ঠিকানা

### Product (পণ্য)
- name: পণ্যের নাম
- category: ক্যাটাগরি (দরজা, জানালা, গ্রিল, গেট, রেলিং, শেড, অন্যান্য)
- image: ছবি
- description: বিবরণ
- estimated_price: আনুমানিক দাম
- is_active: সক্রিয় কিনা
- created_at: তৈরির তারিখ

### Order (অর্ডার)
- customer_name: ক্রেতার নাম
- mobile_number: মোবাইল নাম্বার
- product_name: পণ্যের নাম
- product_description: পণ্যের বিবরণ
- total_price: মোট মূল্য
- cash_paid: নগদ পরিশোধ
- due_amount: বাকি টাকা (অটো ক্যালকুলেশন)
- order_date: অর্ডার নেওয়ার তারিখ
- delivery_date: ডেলিভারির তারিখ
- status: অবস্থা (চলমান/সম্পন্ন)

## Production Deployment

Production এ deploy করার আগে:

১. `settings.py` তে পরিবর্তন করুন:
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
SECRET_KEY = 'নতুন-সিক্রেট-কী-জেনারেট-করুন'
```

২. Static files collect করুন:
```bash
python manage.py collectstatic
```

৩. PostgreSQL ব্যবহার করতে চাইলে `settings.py` এ database সেটিংস পরিবর্তন করুন

## সাপোর্ট

কোনো সমস্যা হলে বা প্রশ্ন থাকলে যোগাযোগ করুন।

## লাইসেন্স

এই প্রোজেক্টটি শুধুমাত্র বাধন স্টিলের জন্য তৈরি করা হয়েছে।

---

**তৈরি করেছেন:** Django Development Team
**তারিখ:** ২০২৪

