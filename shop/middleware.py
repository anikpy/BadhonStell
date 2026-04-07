"""
Rate Limiting Middleware for Badhon Steel
Prevents brute force attacks on login and admin pages
"""

import time
from django.http import HttpResponseForbidden
from django.core.cache import cache


class RateLimitMiddleware:
    """
    Rate limiting middleware to prevent brute force attacks.
    Limits requests per IP address for sensitive endpoints.
    """
    
    # Endpoints to protect (path patterns)
    PROTECTED_ENDPOINTS = [
        '/admin-panel/login/',
        '/admin-panel/',
        '/admin/',
    ]
    
    # Rate limit settings - RELAXED for development
    MAX_REQUESTS = 50  # Maximum requests (increased from 5)
    TIME_WINDOW = 600  # Time window in seconds (10 minutes)
    BLOCK_DURATION = 600  # Block duration in seconds (10 minutes)
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get client IP
        ip_address = self.get_client_ip(request)
        
        # Check if this is a protected endpoint
        if self.is_protected_endpoint(request.path):
            # Check if IP is blocked
            block_key = f'ratelimit_block_{ip_address}'
            if cache.get(block_key):
                return HttpResponseForbidden(
                    '<h1>🚫 Access Blocked</h1>'
                    '<p>Too many requests. Please try again after 10 minutes.</p>'
                    '<p>অনেকবার চেষ্টা করেছেন। ১০ মিনিট পর আবার চেষ্টা করুন।</p>'
                )
            
            # Check rate limit
            rate_key = f'ratelimit_{ip_address}_{request.path}'
            requests = cache.get(rate_key, [])
            
            # Clean old requests outside time window
            current_time = time.time()
            requests = [req_time for req_time in requests 
                       if current_time - req_time < self.TIME_WINDOW]
            
            # Check if limit exceeded
            if len(requests) >= self.MAX_REQUESTS:
                # Block the IP
                cache.set(block_key, True, self.BLOCK_DURATION)
                return HttpResponseForbidden(
                    '<h1>🚫 Access Blocked</h1>'
                    '<p>Too many requests. Please try again after 10 minutes.</p>'
                    '<p>অনেকবার চেষ্টা করেছেন। ১০ মিনিট পর আবার চেষ্টা করুন।</p>'
                )
            
            # Add current request
            requests.append(current_time)
            cache.set(rate_key, requests, self.TIME_WINDOW)
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Get the client's IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'unknown'
    
    def is_protected_endpoint(self, path):
        """Check if the path is a protected endpoint"""
        for endpoint in self.PROTECTED_ENDPOINTS:
            if path.startswith(endpoint):
                return True
        return False


class SecurityHeadersMiddleware:
    """
    Add security headers to all responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Security Headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "frame-ancestors 'none';"
        )
        response['Content-Security-Policy'] = csp
        
        return response
