# 🔒 Security Configuration Guide for Badhon Steel

## ⚠️ CRITICAL SECURITY FIXES APPLIED

Your Django settings have been hardened with production-grade security. Follow this guide to complete the setup.

---

## 1️⃣ Environment Variables (CRITICAL)

Create a `.env` file in your project root (NEVER commit this to git):

```bash
# Generate a strong secret key: python -c "import secrets; print(secrets.token_urlsafe(50))"
DJANGO_SECRET_KEY=your-generated-secret-key-here-change-immediately

# Set to False in production
DJANGO_DEBUG=False

# Enable HTTPS when SSL is configured
DJANGO_HTTPS=True

# Database (PostgreSQL recommended for production)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=badhonsteel_db
DB_USER=badhonsteel_user
DB_PASSWORD=your-strong-db-password-here
DB_HOST=localhost
DB_PORT=5432
```

### Install python-dotenv:
```bash
pip install python-dotenv
```

---

## 2️⃣ Database Security (HIGH PRIORITY)

### PostgreSQL Setup (Production - Required)

**Do NOT use SQLite in production** - it's insecure and not scalable.

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE badhonsteel_db;
CREATE USER badhonsteel_user WITH PASSWORD 'your-strong-password';
GRANT ALL PRIVILEGES ON DATABASE badhonsteel_db TO badhonsteel_user;
\q
```

### Install psycopg2:
```bash
pip install psycopg2-binary
```

---

## 3️⃣ SSL/HTTPS Configuration (CRITICAL)

### Option A: Let's Encrypt (Free SSL)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d badhonsteel.com -d www.badhonsteel.com

# Auto-renewal test
sudo certbot renew --dry-run
```

### Option B: Cloudflare (Easiest)

1. Sign up at cloudflare.com
2. Add your domain `badhonsteel.com`
3. Change nameservers to Cloudflare
4. Enable "Always Use HTTPS" and "Automatic HTTPS Rewrites"

---

## 4️⃣ Nginx Configuration (Production Web Server)

```nginx
# /etc/nginx/sites-available/badhonsteel
server {
    listen 80;
    server_name badhonsteel.com www.badhonsteel.com;
    return 301 https://$server_name$request_uri;  # Redirect HTTP to HTTPS
}

server {
    listen 443 ssl http2;
    server_name badhonsteel.com www.badhonsteel.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/badhonsteel.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/badhonsteel.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; frame-ancestors 'none';" always;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/anik/Personal/BadhonStell/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/anik/Personal/BadhonStell/media/;
        expires 1y;
    }
}
```

---

## 5️⃣ Gunicorn Service (Production Application Server)

```ini
# /etc/systemd/system/badhonsteel.service
[Unit]
Description=Badhon Steel Django Application
After=network.target

[Service]
User=anik
Group=www-data
WorkingDirectory=/home/anik/Personal/BadhonStell
Environment="DJANGO_SECRET_KEY=your-secret-key"
Environment="DJANGO_DEBUG=False"
Environment="DJANGO_HTTPS=True"
Environment="DB_ENGINE=django.db.backends.postgresql"
Environment="DB_NAME=badhonsteel_db"
Environment="DB_USER=badhonsteel_user"
Environment="DB_PASSWORD=your-db-password"
Environment="DB_HOST=localhost"
Environment="DB_PORT=5432"

ExecStart=/home/anik/Personal/BadhonStell/venv/bin/gunicorn \
    --access-logfile - \
    --workers 3 \
    --bind unix:/home/anik/Personal/BadhonStell/app.sock \
    badhonsteel.wsgi:application

[Install]
WantedBy=multi-user.target
```

---

## 6️⃣ Firewall Configuration

```bash
# Enable UFW firewall
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable

# Check status
sudo ufw status
```

---

## 7️⃣ Automatic Security Updates

```bash
# Install unattended-upgrades
sudo apt-get install unattended-upgrades

# Enable automatic security updates
sudo dpkg-reconfigure unattended-upgrades
```

---

## 8️⃣ Backup Strategy (CRITICAL)

```bash
# Create backup script
#!/bin/bash
# /home/anik/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/anik/backups"

# Database backup
pg_dump badhonsteel_db > $BACKUP_DIR/db_$DATE.sql

# Media files backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /home/anik/Personal/BadhonStell/media/

# Keep only last 7 backups
cd $BACKUP_DIR && ls -t db_*.sql | tail -n +8 | xargs rm -f
cd $BACKUP_DIR && ls -t media_*.tar.gz | tail -n +8 | xargs rm -f
```

Add to crontab:
```bash
0 2 * * * /home/anik/backup.sh  # Daily at 2 AM
```

---

## 9️⃣ Security Checklist Before Going Live

- [ ] Change default admin password
- [ ] Remove any test data
- [ ] Generate strong SECRET_KEY
- [ ] Set DEBUG = False
- [ ] Configure ALLOWED_HOSTS
- [ ] Enable HTTPS/SSL
- [ ] Set up PostgreSQL database
- [ ] Configure firewall
- [ ] Enable automatic security updates
- [ ] Set up backups
- [ ] Remove `.env` from git
- [ ] Add `.env` to `.gitignore`
- [ ] Review user permissions

---

## 🔟 Emergency Contacts & Resources

- **Django Security:** https://docs.djangoproject.com/en/stable/topics/security/
- **Let's Encrypt:** https://certbot.eff.org/
- **Cloudflare:** https://www.cloudflare.com/
- **Security Advisories:** https://www.djangoproject.com/weblog/

---

## ⚡ Quick Security Test Commands

```bash
# Check Django security
python manage.py check --deploy

# Test SSL configuration
https://www.ssllabs.com/ssltest/analyze.html?d=badhonsteel.com

# Security headers test
https://securityheaders.com/?q=badhonsteel.com

# Check for vulnerabilities
pip install safety
safety check
```

---

**🔴 IMPORTANT:** Complete all steps before launching to production. Your site is now configured with enterprise-grade security settings!
