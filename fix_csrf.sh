#!/bin/bash
# CSRF Fix Script for Badhon Steel
# Run this on your VPS to fix CSRF issues

echo "=============================================="
echo "CSRF Fix for Badhon Steel"
echo "=============================================="

# Create the correct Nginx config
cat > /tmp/badhonsteel_nginx_fix << 'EOF'
# Fixed Nginx Configuration
# The key change: proxy_set_header X-Forwarded-Proto https; (hardcoded, not $scheme)

server {
    listen 80;
    server_name badhonsteel.com www.badhonsteel.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name badhonsteel.com www.badhonsteel.com;

    ssl_certificate /etc/letsencrypt/live/badhonsteel.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/badhonsteel.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # FIXED: Hardcode https instead of using $scheme
        proxy_set_header X-Forwarded-Proto https;
    }

    location /static/ {
        alias /home/anik/Personal/BadhonStell/staticfiles/;
    }

    location /media/ {
        alias /home/anik/Personal/BadhonStell/media/;
    }
}
EOF

echo ""
echo "1. Nginx config created at /tmp/badhonsteel_nginx_fix"
echo ""
echo "2. To apply the fix, run these commands:"
echo "   sudo cp /tmp/badhonsteel_nginx_fix /etc/nginx/sites-available/badhonsteel"
echo "   sudo nginx -t"
echo "   sudo systemctl restart nginx"
echo ""
echo "3. Make sure your Django settings.py has these:"
echo "   USE_X_FORWARDED_HOST = True"
echo "   SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')"
echo "   CSRF_TRUSTED_ORIGINS = ['https://badhonsteel.com', 'https://www.badhonsteel.com']"
echo "   CSRF_COOKIE_SECURE = False"
echo ""
echo "4. Restart Gunicorn:"
echo "   sudo systemctl restart badhonsteel"
echo ""
echo "=============================================="
echo "The KEY fix is using 'proxy_set_header X-Forwarded-Proto https;'"
echo "instead of 'proxy_set_header X-Forwarded-Proto \$scheme;'"
echo "=============================================="
