# ডাটাবেস স্ট্রাকচার (Database Structure)

## সারসংক্ষেপ

এই প্রোজেক্টে তিনটি প্রধান মডেল রয়েছে:
1. **ShopInfo** - দোকানের তথ্য
2. **Product** - পণ্যের তথ্য
3. **Order** - অর্ডারের তথ্য

---

## ১. ShopInfo Model (দোকানের তথ্য)

দোকানের মূল তথ্য সংরক্ষণ করে।

### ফিল্ডসমূহ:

| ফিল্ড নাম | টাইপ | বর্ণনা | Required |
|-----------|------|--------|----------|
| id | AutoField | Primary Key | ✓ |
| name | CharField(200) | দোকানের নাম | ✓ |
| logo | ImageField | দোকানের লোগো | ✗ |
| description | TextField | দোকানের বিবরণ | ✓ |
| phone | CharField(20) | ফোন নাম্বার | ✓ |
| whatsapp | CharField(20) | হোয়াটসঅ্যাপ নাম্বার | ✓ |
| address | TextField | ঠিকানা | ✗ |

### উদাহরণ ডাটা:

```python
{
    "name": "বাধন স্টিল",
    "description": "স্টিল ও লোহার সকল ধরনের কাজ করা হয়",
    "phone": "01712345678",
    "whatsapp": "01712345678",
    "address": "ঢাকা, বাংলাদেশ"
}
```

---

## ২. Product Model (পণ্য)

পণ্যের তথ্য সংরক্ষণ করে।

### ফিল্ডসমূহ:

| ফিল্ড নাম | টাইপ | বর্ণনা | Required |
|-----------|------|--------|----------|
| id | AutoField | Primary Key | ✓ |
| name | CharField(200) | পণ্যের নাম | ✓ |
| category | CharField(50) | ক্যাটাগরি | ✓ |
| image | ImageField | পণ্যের ছবি | ✓ |
| description | TextField | পণ্যের বিবরণ | ✓ |
| estimated_price | DecimalField(10,2) | আনুমানিক দাম | ✓ |
| is_active | BooleanField | সক্রিয় কিনা | ✓ (default: True) |
| created_at | DateTimeField | তৈরির তারিখ | ✓ (auto) |

### ক্যাটাগরি চয়েস:

| Value | Display |
|-------|---------|
| door | দরজা |
| window | জানালা |
| grill | গ্রিল |
| gate | গেট |
| railing | রেলিং |
| shed | শেড |
| other | অন্যান্য |

### উদাহরণ ডাটা:

```python
{
    "name": "স্টিল দরজা",
    "category": "door",
    "description": "উচ্চমানের স্টিল দরজা, টেকসই এবং নিরাপদ",
    "estimated_price": 15000.00,
    "is_active": True
}
```

---

## ৩. Order Model (অর্ডার)

অর্ডারের সম্পূর্ণ তথ্য সংরক্ষণ করে।

### ফিল্ডসমূহ:

| ফিল্ড নাম | টাইপ | বর্ণনা | Required | Auto Calculate |
|-----------|------|--------|----------|----------------|
| id | AutoField | Primary Key | ✓ | - |
| customer_name | CharField(200) | ক্রেতার নাম | ✓ | - |
| mobile_number | CharField(20) | মোবাইল নাম্বার | ✓ | - |
| product_name | CharField(200) | পণ্যের নাম | ✓ | - |
| product_description | TextField | পণ্যের বিবরণ | ✓ | - |
| total_price | DecimalField(10,2) | মোট মূল্য | ✓ | - |
| cash_paid | DecimalField(10,2) | নগদ পরিশোধ | ✓ | - |
| due_amount | DecimalField(10,2) | বাকি টাকা | ✓ | ✓ (total - cash) |
| order_date | DateField | অর্ডার তারিখ | ✓ | - |
| delivery_date | DateField | ডেলিভারি তারিখ | ✓ | - |
| status | CharField(20) | অবস্থা | ✓ (default: pending) | - |
| created_at | DateTimeField | তৈরির সময় | ✓ (auto) | - |
| updated_at | DateTimeField | আপডেটের সময় | ✓ (auto) | - |

### স্ট্যাটাস চয়েস:

| Value | Display |
|-------|---------|
| pending | চলমান |
| completed | সম্পন্ন |

### বাকি টাকা ক্যালকুলেশন:

```python
due_amount = total_price - cash_paid
```

এটি স্বয়ংক্রিয়ভাবে `save()` মেথডে হিসাব হয়।

### উদাহরণ ডাটা:

```python
{
    "customer_name": "মোঃ রহিম",
    "mobile_number": "01712345678",
    "product_name": "স্টিল দরজা",
    "product_description": "৭ ফুট x ৪ ফুট, সাদা রঙের",
    "total_price": 15000.00,
    "cash_paid": 10000.00,
    "due_amount": 5000.00,  # Auto calculated
    "order_date": "2024-01-15",
    "delivery_date": "2024-01-25",
    "status": "pending"
}
```

---

## ডাটাবেস রিলেশনশিপ

এই প্রোজেক্টে কোনো Foreign Key রিলেশনশিপ নেই। সব মডেল স্বাধীন।

### কেন Foreign Key ব্যবহার করা হয়নি?

1. **সরলতা:** ছোট ব্যবসার জন্য সহজ রাখা হয়েছে
2. **নমনীয়তা:** পণ্য ডিলিট করলেও অর্ডার থাকবে
3. **কাস্টমাইজেশন:** প্রতিটি অর্ডারে কাস্টম পণ্যের বিবরণ দেওয়া যায়

---

## SQL Schema (SQLite)

### ShopInfo Table

```sql
CREATE TABLE shop_shopinfo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    logo VARCHAR(100),
    description TEXT NOT NULL,
    phone VARCHAR(20) NOT NULL,
    whatsapp VARCHAR(20) NOT NULL,
    address TEXT
);
```

### Product Table

```sql
CREATE TABLE shop_product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    image VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    estimated_price DECIMAL(10, 2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL
);
```

### Order Table

```sql
CREATE TABLE shop_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name VARCHAR(200) NOT NULL,
    mobile_number VARCHAR(20) NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    product_description TEXT NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    cash_paid DECIMAL(10, 2) NOT NULL,
    due_amount DECIMAL(10, 2) NOT NULL,
    order_date DATE NOT NULL,
    delivery_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

---

## ইনডেক্স (Indexes)

Django স্বয়ংক্রিয়ভাবে নিচের ইনডেক্স তৈরি করে:

1. Primary Key (id) - সব টেবিলে
2. created_at - Product এবং Order টেবিলে (ordering এর জন্য)

---

## ডাটা ভ্যালিডেশন

### Product Model:
- `estimated_price` অবশ্যই পজিটিভ হতে হবে
- `category` অবশ্যই নির্ধারিত চয়েস থেকে হতে হবে

### Order Model:
- `cash_paid` অবশ্যই `total_price` এর সমান বা কম হতে হবে
- `delivery_date` অবশ্যই `order_date` এর পরে হতে হবে (ভবিষ্যতে যোগ করা যেতে পারে)

---

## ব্যাকআপ নির্দেশিকা

### SQLite Database Backup:

```bash
# ব্যাকআপ তৈরি
cp db.sqlite3 backup_$(date +%Y%m%d).sqlite3

# রিস্টোর
cp backup_20240115.sqlite3 db.sqlite3
```

### Django Fixtures:

```bash
# ডাটা এক্সপোর্ট
python manage.py dumpdata shop > backup.json

# ডাটা ইম্পোর্ট
python manage.py loaddata backup.json
```

---

**শেষ আপডেট:** ২০২৪

