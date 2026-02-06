@echo off
echo ==========================================
echo বাধন স্টিল - সেটআপ স্ক্রিপ্ট (Windows)
echo ==========================================
echo.

REM Virtual environment সক্রিয় করা
if exist "venv\" (
    echo ✓ Virtual environment পাওয়া গেছে
    call venv\Scripts\activate
) else (
    echo ✗ Virtual environment পাওয়া যায়নি
    echo প্রথমে virtual environment তৈরি করুন: python -m venv venv
    pause
    exit /b 1
)

REM প্যাকেজ ইনস্টল
echo.
echo 📦 প্রয়োজনীয় প্যাকেজ ইনস্টল করা হচ্ছে...
pip install -r requirements.txt

REM Migrations
echo.
echo 🗄️ Database migrations তৈরি করা হচ্ছে...
python manage.py makemigrations

echo.
echo 🗄️ Database migrations প্রয়োগ করা হচ্ছে...
python manage.py migrate

REM Static files
echo.
echo 📁 Static files collect করা হচ্ছে...
python manage.py collectstatic --noinput

echo.
echo ==========================================
echo ✅ সেটআপ সম্পন্ন হয়েছে!
echo ==========================================
echo.
echo পরবর্তী ধাপ:
echo 1. Superuser তৈরি করুন: python manage.py createsuperuser
echo 2. সার্ভার চালু করুন: python manage.py runserver
echo 3. ব্রাউজারে খুলুন: http://127.0.0.1:8000/
echo.
pause

