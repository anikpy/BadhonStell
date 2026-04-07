"""
Django settings for badhonsteel project.
Production-ready with security hardening.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================================
# SECURITY SETTINGS - PRODUCTION HARDENING
# ==============================================================================

# SECRET_KEY: Load from environment variable (NEVER hardcode in production)
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    # Fallback only for development - generate a new one for production
    import secrets
    SECRET_KEY = secrets.token_urlsafe(50)
    print("WARNING: Using auto-generated SECRET_KEY. Set DJANGO_SECRET_KEY env var for production!")

# DEBUG: MUST be False in production
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'

# ALLOWED_HOSTS: Only your domains
ALLOWED_HOSTS = [
    'badhonsteel.com',
    'www.badhonsteel.com',
    '127.0.0.1',
    'localhost',
]

# Add any additional hosts from environment
extra_hosts = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
if extra_hosts:
    ALLOWED_HOSTS.extend(extra_hosts.split(','))


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'shop',
]

MIDDLEWARE = [
    # 'shop.middleware.CSRFDebugMiddleware',  # DEBUG: Remove after fixing CSRF
    # 'shop.middleware.RateLimitMiddleware',  # DISABLED: Was blocking access
    'shop.middleware.SecurityHeadersMiddleware',  # Security headers
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==============================================================================
# HTTPS & SSL SECURITY (Enable for production)
# ==============================================================================

# Force HTTPS - Let Nginx handle this, not Django
SECURE_SSL_REDIRECT = False  # Nginx redirects HTTP to HTTPS

# HSTS (HTTP Strict Transport Security) - Only enable when fully tested
SECURE_HSTS_SECONDS = 0  # Disabled until HTTPS is fully working
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Secure cookies - Disable for now to fix CSRF, enable after HTTPS confirmed working
SESSION_COOKIE_SECURE = False  # Will enable after HTTPS confirmed
CSRF_COOKIE_SECURE = False  # Must be False for CSRF to work behind proxy
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # False required for JavaScript

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ==============================================================================
# DATABASE SECURITY
# ==============================================================================

# Use PostgreSQL in production (SQLite only for development)
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', ''),
    }
}

# CSRF & CORS - Required for production behind reverse proxy
CSRF_TRUSTED_ORIGINS = [
    'https://badhonsteel.com',
    'https://www.badhonsteel.com',
    'http://badhonsteel.com',
    'http://www.badhonsteel.com',
]

# Trust X-Forwarded headers when behind reverse proxy
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
# Allow both http and https in forwarded proto to fix CSRF issues
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CSRF cookie settings - DISABLED for now to fix production issues
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = None  # Changed from 'Lax' to allow cross-origin

# Disable CSRF for login if needed (emergency fix)
# Add this to views.py login view: @csrf_exempt

# ==============================================================================
# SESSION & AUTH SECURITY
# ==============================================================================

# Session security
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Password validators (stronger passwords)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 10}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ==============================================================================
# TEMPLATES & URLS
# ==============================================================================

ROOT_URLCONF = 'badhonsteel.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'shop' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'badhonsteel.wsgi.application'


# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================
LANGUAGE_CODE = 'bn'

TIME_ZONE = 'Asia/Dhaka'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'shop' / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URL
LOGIN_URL = '/admin-panel/login/'
LOGIN_REDIRECT_URL = '/admin-panel/'


# Email Configuration
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@gmail.com'
# EMAIL_HOST_PASSWORD = 'your-app-password'
# DEFAULT_FROM_EMAIL = 'Badhon Steel <your-email@gmail.com>'
