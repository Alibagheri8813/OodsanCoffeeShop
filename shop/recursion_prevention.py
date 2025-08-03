"""
Recursion Prevention Middleware
Prevents infinite loops and recursion errors in the Django application
"""
import threading
import time
import logging
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class RecursionPreventionMiddleware(MiddlewareMixin):
    """
    Middleware to prevent infinite recursion and URL loops
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Thread-local storage for tracking requests
        self.local = threading.local()
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Track request paths to detect loops
        """
        # Initialize request tracking for this thread
        if not hasattr(self.local, 'request_stack'):
            self.local.request_stack = []
            self.local.start_time = time.time()
        
        current_path = request.path
        
        # Check for immediate loops (same path called repeatedly)
        if len(self.local.request_stack) > 0:
            if current_path == self.local.request_stack[-1]:
                count = sum(1 for path in self.local.request_stack if path == current_path)
                if count > 3:  # Allow up to 3 redirects
                    logger.error(f"Potential infinite loop detected for path: {current_path}")
                    return self._handle_recursion_error(request, current_path)
        
        # Check for deep recursion (too many nested requests)
        if len(self.local.request_stack) > 20:
            logger.error(f"Deep recursion detected. Stack: {self.local.request_stack}")
            return self._handle_recursion_error(request, current_path)
        
        # Check for long-running request chains
        if hasattr(self.local, 'start_time'):
            if time.time() - self.local.start_time > 30:  # 30 seconds timeout
                logger.error(f"Request chain timeout. Current path: {current_path}")
                return self._handle_recursion_error(request, current_path)
        
        # Add current path to stack
        self.local.request_stack.append(current_path)
        
        return None
    
    def process_response(self, request, response):
        """
        Clean up request tracking
        """
        if hasattr(self.local, 'request_stack') and self.local.request_stack:
            self.local.request_stack.pop()
            
            # Reset if stack is empty
            if not self.local.request_stack:
                self.local.start_time = time.time()
        
        return response
    
    def process_exception(self, request, exception):
        """
        Handle recursion errors specifically
        """
        if isinstance(exception, RecursionError):
            logger.error(f"RecursionError caught for path: {request.path}")
            return self._handle_recursion_error(request, request.path)
        
        return None
    
    def _handle_recursion_error(self, request, path):
        """
        Handle recursion errors with user-friendly response
        """
        # Clear the request stack to prevent further issues
        if hasattr(self.local, 'request_stack'):
            self.local.request_stack.clear()
        
        # For AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'خطای بازگشت بی‌نهایت شناسایی شد.',
                'redirect': '/shop/',
                'success': False
            }, status=500)
        
        # For regular requests, render error page
        context = {
            'error_message': 'متأسفانه خطای بازگشت بی‌نهایت شناسایی شد.',
            'safe_url': '/shop/',
            'problematic_path': path
        }
        
        try:
            return render(request, 'shop/recursion_error.html', context, status=500)
        except:
            # If template rendering fails, return simple HTML response
            html = f"""
            <!DOCTYPE html>
            <html dir="rtl">
            <head>
                <title>خطای سیستم</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: 'Vazirmatn', Arial; text-align: center; margin: 50px; }}
                    .error {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="error">
                    <h1>خطای سیستم</h1>
                    <p>متأسفانه خطای بازگشت بی‌نهایت شناسایی شد.</p>
                    <a href="/shop/">بازگشت به صفحه اصلی</a>
                </div>
            </body>
            </html>
            """
            return HttpResponse(html, status=500)

class SafeURLRedirectMiddleware(MiddlewareMixin):
    """
    Middleware to handle safe URL redirects and prevent loops
    """
    
    def process_request(self, request):
        """
        Check for problematic URL patterns
        """
        path = request.path
        
        # If accessing root and there's a loop risk, redirect to safe path
        if path == '/' and request.GET.get('loop_prevention'):
            return HttpResponse("Loop prevention activated", status=200)
        
        # Add loop prevention parameter for potentially problematic paths
        if path in ['/', '/home/'] and 'loop_prevention' not in request.GET:
            # Check if this is a redirect from video intro
            referer = request.META.get('HTTP_REFERER', '')
            if 'video_intro' in referer or path == '/':
                # Safe redirect to avoid loops
                from django.shortcuts import redirect
                return redirect('/shop/')
        
        return None