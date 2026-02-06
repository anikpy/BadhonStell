# দ্রুত শুরু করার গাইড (Quick Start Guide)

## ৫ মিনিটে প্রোজেক্ট চালু করুন!

### ধাপ ১: Virtual Environment সক্রিয় করুন

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### ধাপ ২: প্যাকেজ ইনস্টল করুন

```bash
pip install -r requirements.txt
```

### ধাপ ৩: Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
```

### ধাপ ৪: Admin User তৈরি করুন

```bash
python manage.py createsuperuser
```

**উদাহরণ:**
- Username: `admin`
- Email: `admin@badhonsteel.com`
- Password: `admin123` (নিজের পছন্দমত দিন)

### ধাপ ৫: দোকানের তথ্য যোগ করুন

```bash
python manage.py shell
```

Shell এ এই কোড রান করুন:

```python
from shop.models import ShopInfo

ShopInfo.objects.create(
    name='বাধন স্টিল',
    description='স্টিল ও লোহার সকল ধরনের কাজ করা হয়',
    phone='01712345678',
    whatsapp='01712345678',
    address='ঢাকা, বাংলাদেশ'
)

exit()
```

### ধাপ ৬: সার্ভার চালু করুন

```bash
python manage.py runserver
```

### ধাপ ৭: ব্রাউজারে খুলুন

- **কাস্টমার সাইট:** http://127.0.0.1:8000/
- **অ্যাডমিন প্যানেল:** http://127.0.0.1:8000/admin-panel/login/
- **Django Admin:** http://127.0.0.1:8000/django-admin/

---

## অটোমেটিক সেটআপ (Linux/Mac)

```bash
chmod +x setup.sh
./setup.sh
```

## অটোমেটিক সেটআপ (Windows)

```bash
setup.bat
```

---

## প্রথম পণ্য যোগ করুন

১. Django Admin এ যান: http://127.0.0.1:8000/django-admin/
২. Login করুন (admin username/password দিয়ে)
৩. "পণ্যসমূহ" এ ক্লিক করুন
৪. "পণ্য যোগ করুন" ক্লিক করুন
৫. তথ্য পূরণ করুন:
   - নাম: `স্টিল দরজা`
   - ক্যাটাগরি: `দরজা`
   - বিবরণ: `উচ্চমানের স্টিল দরজা`
   - আনুমানিক দাম: `15000`
   - সক্রিয়: ✓ চেক করুন
৬. "সংরক্ষণ করুন" ক্লিক করুন

---

## প্রথম অর্ডার তৈরি করুন

১. অ্যাডমিন প্যানেলে যান: http://127.0.0.1:8000/admin-panel/login/
২. Login করুন
৩. "নতুন অর্ডার" ক্লিক করুন
৪. ফর্ম পূরণ করুন:
   - ক্রেতার নাম: `মোঃ রহিম`
   - মোবাইল: `01712345678`
   - পণ্যের নাম: `স্টিল দরজা`
   - বিবরণ: `৭ ফুট x ৪ ফুট`
   - মোট মূল্য: `15000`
   - নগদ পরিশোধ: `10000`
   - তারিখ নির্বাচন করুন
৫. "অর্ডার তৈরি করুন" ক্লিক করুন

---

## ভাউচার প্রিন্ট করুন

১. অর্ডার তালিকায় যান
২. যেকোনো অর্ডারের "ভাউচার" বাটনে ক্লিক করুন
৩. "প্রিন্ট করুন" বাটনে ক্লিক করুন

---

## সমস্যা সমাধান

### Port already in use
```bash
python manage.py runserver 8001
```

### Migration Error
```bash
python manage.py makemigrations --empty shop
python manage.py migrate
```

### Static files not loading
```bash
python manage.py collectstatic
```

---

## সাহায্য প্রয়োজন?

সম্পূর্ণ ডকুমেন্টেশনের জন্য `README.md` দেখুন।

---

**শুভকামনা! 🎉**

