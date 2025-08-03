import logging
import traceback
from django.http import JsonResponse, HttpResponseServerError
from django.shortcuts import render
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Enhanced error handling middleware with logging and user-friendly error pages
    """
    
    def process_exception(self, request, exception):
        """
        Handle exceptions with proper logging and user-friendly responses
        """
        # Log the exception with full traceback
        logger.error(
            f"Exception occurred: {exception}\n"
            f"URL: {request.build_absolute_uri()}\n"
            f"User: {request.user if hasattr(request, 'user') else 'Anonymous'}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        
        # For AJAX requests, return JSON error response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            error_message = "متأسفانه خطایی رخ داده است. لطفاً دوباره تلاش کنید."
            if settings.DEBUG:
                error_message = str(exception)
            
            return JsonResponse({
                'success': False,
                'error': error_message,
                'type': exception.__class__.__name__
            }, status=500)
        
        # For regular requests, return custom error page
        context = {
            'error_type': exception.__class__.__name__,
            'error_message': "متأسفانه خطایی رخ داده است. لطفاً دوباره تلاش کنید.",
            'debug': settings.DEBUG,
            'exception': exception if settings.DEBUG else None
        }
        
        return render(request, 'shop/error.html', context, status=500)

class SecurityMiddleware(MiddlewareMixin):
    """
    Enhanced security middleware for the coffee shop application
    """
    
    def process_request(self, request):
        """
        Add security headers and check for suspicious activity
        """
        # Log suspicious requests
        if self._is_suspicious_request(request):
            logger.warning(
                f"Suspicious request detected: {request.build_absolute_uri()}\n"
                f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}\n"
                f"IP: {self._get_client_ip(request)}"
            )
    
    def process_response(self, request, response):
        """
        Add security headers to response
        """
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
    
    def _is_suspicious_request(self, request):
        """
        Check for suspicious request patterns
        """
        suspicious_patterns = [
            'admin', 'wp-admin', '.php', 'phpmyadmin', 
            'xmlrpc', 'wp-login', 'config', '.env'
        ]
        
        path = request.path.lower()
        return any(pattern in path for pattern in suspicious_patterns)
    
    def _get_client_ip(self, request):
        """
        Get the real client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Monitor performance and log slow requests
    """
    
    def process_request(self, request):
        """
        Start timing the request
        """
        import time
        request._start_time = time.time()
    
    def process_response(self, request, response):
        """
        Log slow requests
        """
        if hasattr(request, '_start_time'):
            import time
            duration = time.time() - request._start_time
            
            # Log slow requests (> 2 seconds)
            if duration > 2.0:
                logger.warning(
                    f"Slow request detected: {request.build_absolute_uri()}\n"
                    f"Duration: {duration:.2f}s\n"
                    f"User: {request.user if hasattr(request, 'user') else 'Anonymous'}"
                )
            
            # Add performance header for monitoring
            response['X-Response-Time'] = f"{duration:.3f}s"
        
        return response