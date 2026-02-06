# বাধন স্টিল - প্রোজেক্ট সামারি

## 📋 প্রোজেক্ট ওভারভিউ

এটি একটি সম্পূর্ণ **Production-Ready** Django ওয়েব অ্যাপ্লিকেশন যা স্টিল ও লোহার দোকানের জন্য তৈরি করা হয়েছে।

### ✨ মূল ফিচারসমূহ

#### 🛍️ কাস্টমার সাইট
- আকর্ষণীয় হোম পেজ
- পণ্য তালিকা (ক্যাটাগরি ফিল্টার সহ)
- সরাসরি ফোন ও হোয়াটসঅ্যাপে যোগাযোগ
- সম্পূর্ণ বাংলা ইন্টারফেস
- Responsive Design

#### 🔐 কাস্টম অ্যাডমিন প্যানেল
- সুরক্ষিত লগইন সিস্টেম
- ইন্টারঅ্যাক্টিভ ড্যাশবোর্ড
- অর্ডার ম্যানেজমেন্ট (CRUD)
- উন্নত সার্চ ফিচার
- প্রিন্টযোগ্য ভাউচার/ইনভয়েস
- বাকি টাকা অটো ক্যালকুলেশন

---

## 📁 প্রোজেক্ট স্ট্রাকচার

```
BadhonStell/
├── badhonsteel/              # Main project directory
│   ├── __init__.py
│   ├── settings.py           # Project settings
│   ├── urls.py               # Main URL configuration
│   ├── wsgi.py
│   └── asgi.py
│
├── shop/                     # Main app
│   ├── migrations/           # Database migrations
│   ├── templates/            # HTML templates
│   │   ├── base.html
│   │   ├── shop/             # Customer site templates
│   │   │   ├── home.html
│   │   │   └── products.html
│   │   └── admin_panel/      # Admin panel templates
│   │       ├── base.html
│   │       ├── login.html
│   │       ├── dashboard.html
│   │       ├── order_list.html
│   │       ├── order_form.html
│   │       └── voucher.html
│   ├── static/               # Static files
│   │   └── css/
│   │       └── style.css
│   ├── models.py             # Database models
│   ├── views.py              # View functions
│   ├── urls.py               # App URLs
│   ├── forms.py              # Forms
│   └── admin.py              # Django admin config
│
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── create_sample_data.py     # Sample data creation script
├── create_admin.py           # Admin user creation script
├── setup.sh                  # Setup script (Linux/Mac)
├── setup.bat                 # Setup script (Windows)
│
├── README.md                 # Main documentation
├── QUICKSTART.md             # Quick start guide
├── DATABASE_STRUCTURE.md     # Database documentation
└── PROJECT_SUMMARY.md        # This file
```

---

## 🗄️ ডাটাবেস মডেল

### 1. ShopInfo (দোকানের তথ্য)
- দোকানের নাম, ফোন, হোয়াটসঅ্যাপ, ঠিকানা

### 2. Product (পণ্য)
- নাম, ক্যাটাগরি, বিবরণ, দাম
- ক্যাটাগরি: দরজা, জানালা, গ্রিল, গেট, রেলিং, শেড, অন্যান্য

### 3. Order (অর্ডার)
- ক্রেতার তথ্য, পণ্যের তথ্য
- মূল্য, নগদ, বাকি (অটো ক্যালকুলেশন)
- তারিখ, স্ট্যাটাস

---

## 🚀 দ্রুত শুরু করুন

### ১. Virtual Environment সক্রিয় করুন
```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### ২. Dependencies ইনস্টল করুন
```bash
pip install -r requirements.txt
```

### ৩. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### ৪. Admin User তৈরি করুন
```bash
python create_admin.py
```
**Credentials:** Username: `admin`, Password: `admin123`

### ৫. Sample Data তৈরি করুন (Optional)
```bash
python create_sample_data.py
```

### ৬. সার্ভার চালু করুন
```bash
python manage.py runserver
```

### ৭. ব্রাউজারে খুলুন
- **কাস্টমার সাইট:** http://127.0.0.1:8000/
- **অ্যাডমিন প্যানেল:** http://127.0.0.1:8000/admin-panel/login/
- **Django Admin:** http://127.0.0.1:8000/django-admin/

---

## 🎯 URL স্ট্রাকচার

### কাস্টমার সাইট
- `/` - হোম পেজ
- `/products/` - পণ্য তালিকা
- `/products/?category=door` - ক্যাটাগরি ফিল্টার

### অ্যাডমিন প্যানেল
- `/admin-panel/login/` - লগইন
- `/admin-panel/` - ড্যাশবোর্ড
- `/admin-panel/orders/` - অর্ডার তালিকা
- `/admin-panel/orders/create/` - নতুন অর্ডার
- `/admin-panel/orders/<id>/edit/` - অর্ডার সম্পাদনা
- `/admin-panel/orders/<id>/voucher/` - ভাউচার প্রিন্ট
- `/admin-panel/orders/<id>/complete/` - অর্ডার সম্পন্ন

---

## 🛠️ প্রযুক্তি স্ট্যাক

- **Backend:** Django 4.2+
- **Database:** SQLite (ডিফল্ট)
- **Frontend:** HTML5, CSS3
- **Font:** Google Fonts (Noto Sans Bengali)
- **Icons:** Unicode Emoji

---

## 📊 ফিচার চেকলিস্ট

### কাস্টমার সাইট
- [x] হোম পেজ
- [x] পণ্য তালিকা
- [x] ক্যাটাগরি ফিল্টার
- [x] ফোন/হোয়াটসঅ্যাপ যোগাযোগ
- [x] Responsive Design
- [x] বাংলা ফন্ট সাপোর্ট

### অ্যাডমিন প্যানেল
- [x] লগইন/লগআউট
- [x] ড্যাশবোর্ড (পরিসংখ্যান)
- [x] অর্ডার তৈরি
- [x] অর্ডার সম্পাদনা
- [x] অর্ডার মুছে ফেলা
- [x] অর্ডার সম্পন্ন করা
- [x] সার্চ (নাম, মোবাইল, পণ্য)
- [x] স্ট্যাটাস ফিল্টার
- [x] প্রিন্টযোগ্য ভাউচার
- [x] বাকি টাকা অটো ক্যালকুলেশন

### অন্যান্য
- [x] Sample Data Script
- [x] Admin Creation Script
- [x] Setup Scripts
- [x] সম্পূর্ণ ডকুমেন্টেশন

---

## 🔒 নিরাপত্তা

### Production এ Deploy করার আগে:

1. **SECRET_KEY পরিবর্তন করুন**
   ```python
   # settings.py
   SECRET_KEY = 'নতুন-র্যান্ডম-সিক্রেট-কী'
   ```

2. **DEBUG বন্ধ করুন**
   ```python
   DEBUG = False
   ```

3. **ALLOWED_HOSTS সেট করুন**
   ```python
   ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
   ```

4. **Admin পাসওয়ার্ড পরিবর্তন করুন**

5. **HTTPS ব্যবহার করুন**

---

## 📝 কাস্টমাইজেশন

### দোকানের তথ্য পরিবর্তন
Django Admin থেকে ShopInfo মডেল এডিট করুন।

### পণ্য যোগ/সম্পাদনা
Django Admin থেকে Product মডেল ম্যানেজ করুন।

### ডিজাইন পরিবর্তন
`shop/templates/` এবং `shop/static/css/` ফাইল এডিট করুন।

---

## 🐛 সমস্যা সমাধান

### Port already in use
```bash
python manage.py runserver 8001
```

### Static files not loading
```bash
python manage.py collectstatic
```

### Migration errors
```bash
python manage.py makemigrations --empty shop
python manage.py migrate
```

---

## 📞 সাপোর্ট

বিস্তারিত ডকুমেন্টেশনের জন্য দেখুন:
- `README.md` - সম্পূর্ণ গাইড
- `QUICKSTART.md` - দ্রুত শুরু
- `DATABASE_STRUCTURE.md` - ডাটাবেস তথ্য

---

## 📄 লাইসেন্স

এই প্রোজেক্টটি বাধন স্টিলের জন্য তৈরি করা হয়েছে।

---

**তৈরি করেছেন:** Django Development Team  
**তারিখ:** ২০২৪  
**ভার্সন:** 1.0.0

