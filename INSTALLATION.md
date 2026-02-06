# ইনস্টলেশন গাইড

## সিস্টেম রিকোয়ারমেন্ট

- Python 3.8 বা তার উপরের ভার্সন
- pip (Python package manager)
- Virtual Environment (সুপারিশকৃত)

---

## ধাপে ধাপে ইনস্টলেশন

### ১. Python ইনস্টল করুন

#### Windows:
1. https://www.python.org/downloads/ থেকে Python ডাউনলোড করুন
2. ইনস্টলারে "Add Python to PATH" চেক করুন
3. ইনস্টল করুন

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

#### Mac:
```bash
brew install python3
```

### ২. প্রোজেক্ট ডাউনলোড করুন

```bash
# যদি Git থাকে
git clone <repository-url>
cd BadhonStell

# অথবা ZIP ডাউনলোড করে extract করুন
```

### ৩. Virtual Environment তৈরি করুন

```bash
# Virtual environment তৈরি
python -m venv venv

# অথবা Python 3 এর জন্য
python3 -m venv venv
```

### ৪. Virtual Environment সক্রিয় করুন

#### Linux/Mac:
```bash
source venv/bin/activate
```

#### Windows (Command Prompt):
```bash
venv\Scripts\activate
```

#### Windows (PowerShell):
```bash
venv\Scripts\Activate.ps1
```

**নোট:** সফলভাবে সক্রিয় হলে terminal এ `(venv)` দেখাবে।

### ৫. Dependencies ইনস্টল করুন

```bash
pip install -r requirements.txt
```

**যদি Pillow ইনস্টল করতে চান (ছবি আপলোডের জন্য):**
```bash
pip install Pillow
```

তারপর `shop/models.py` ফাইলে ImageField uncomment করুন।

### ৬. Database Setup

```bash
# Migrations তৈরি করুন
python manage.py makemigrations

# Database তৈরি করুন
python manage.py migrate
```

### ৭. Admin User তৈরি করুন

**Option A: স্ক্রিপ্ট ব্যবহার করে (সহজ)**
```bash
python create_admin.py
```

**Option B: ম্যানুয়ালি**
```bash
python manage.py createsuperuser
```

তারপর Username, Email, Password দিন।

### ৮. Sample Data তৈরি করুন (Optional)

```bash
python create_sample_data.py
```

এটি তৈরি করবে:
- দোকানের তথ্য
- ৮টি নমুনা পণ্য
- ৪টি নমুনা অর্ডার

### ৯. সার্ভার চালু করুন

```bash
python manage.py runserver
```

### ১০. ব্রাউজারে খুলুন

- **কাস্টমার সাইট:** http://127.0.0.1:8000/
- **অ্যাডমিন প্যানেল:** http://127.0.0.1:8000/admin-panel/login/
- **Django Admin:** http://127.0.0.1:8000/django-admin/

**লগইন তথ্য (যদি create_admin.py ব্যবহার করেন):**
- Username: `admin`
- Password: `admin123`

---

## অটোমেটিক সেটআপ

### Linux/Mac:

```bash
chmod +x setup.sh
./setup.sh
```

### Windows:

```bash
setup.bat
```

এই স্ক্রিপ্ট স্বয়ংক্রিয়ভাবে করবে:
- Dependencies ইনস্টল
- Database migrations
- Static files collect

তারপর শুধু admin user তৈরি করুন এবং সার্ভার চালু করুন।

---

## সমস্যা সমাধান

### ১. "python: command not found"

**সমাধান:** `python3` ব্যবহার করুন
```bash
python3 manage.py runserver
```

### ২. "pip: command not found"

**সমাধান:**
```bash
# Linux/Mac
python3 -m pip install -r requirements.txt

# Windows
python -m pip install -r requirements.txt
```

### ৩. "Permission denied" (Linux/Mac)

**সমাধান:**
```bash
chmod +x setup.sh
chmod +x manage.py
```

### ৪. Virtual Environment সক্রিয় হচ্ছে না (Windows PowerShell)

**সমাধান:**
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### ৫. Port 8000 already in use

**সমাধান:**
```bash
python manage.py runserver 8001
```

### ৬. Static files লোড হচ্ছে না

**সমাধান:**
```bash
python manage.py collectstatic
```

### ৭. Database locked error

**সমাধান:**
- সার্ভার বন্ধ করুন (Ctrl+C)
- আবার চালু করুন

---

## আনইনস্টল

### Virtual Environment সহ সব মুছে ফেলতে:

```bash
# Virtual environment deactivate করুন
deactivate

# প্রোজেক্ট ফোল্ডার মুছে ফেলুন
rm -rf BadhonStell  # Linux/Mac
rmdir /s BadhonStell  # Windows
```

---

## পরবর্তী ধাপ

ইনস্টলেশন সম্পন্ন হলে:

1. **দোকানের তথ্য যোগ করুন**
   - Django Admin এ যান
   - ShopInfo যোগ করুন

2. **পণ্য যোগ করুন**
   - Django Admin এ Product যোগ করুন

3. **অর্ডার তৈরি করুন**
   - অ্যাডমিন প্যানেলে লগইন করুন
   - নতুন অর্ডার তৈরি করুন

4. **ডকুমেন্টেশন পড়ুন**
   - `README.md` - সম্পূর্ণ গাইড
   - `QUICKSTART.md` - দ্রুত শুরু
   - `DATABASE_STRUCTURE.md` - ডাটাবেস তথ্য

---

## সাহায্য প্রয়োজন?

- `README.md` দেখুন
- `QUICKSTART.md` দেখুন
- Django ডকুমেন্টেশন: https://docs.djangoproject.com/

---

**শুভকামনা! 🎉**

