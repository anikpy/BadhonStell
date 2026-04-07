"""
CSRF Debug View - Check what's happening with headers
Add this to shop/urls.py temporarily
then visit: /admin-panel/csrf-debug/
"""

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


@login_required
def csrf_debug_view(request):
    """Debug view to check CSRF-related headers"""
    headers = {
        'host': request.get_host(),
        'scheme': request.scheme,
        'is_secure': request.is_secure(),
        'path': request.path,
        'method': request.method,
    }
    
    # Get all relevant META headers
    meta_headers = {}
    for key, value in request.META.items():
        if key.startswith('HTTP_') or key in ['SERVER_NAME', 'SERVER_PORT', 'REMOTE_ADDR']:
            meta_headers[key] = str(value)
    
    # CSRF specific
    csrf_token = request.META.get('CSRF_COOKIE', 'Not set')
    
    response_data = {
        'request_info': headers,
        'csrf_cookie': csrf_token,
        'all_headers': meta_headers,
        'csrf_trusted_origins': [
            'https://badhonsteel.com',
            'https://www.badhonsteel.com',
            'http://badhonsteel.com',
            'http://www.badhonsteel.com',
        ],
        'recommended_nginx_config': """
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
"""
    }
    
    return JsonResponse(response_data, json_dumps_params={'indent': 2})


# Add to urls.py:
# path('admin-panel/csrf-debug/', views.csrf_debug_view, name='csrf_debug'),
