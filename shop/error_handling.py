import logging
import traceback
import time
from functools import wraps
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.core.cache import cache
from django.db import transaction, DatabaseError, IntegrityError
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)

# Performance monitoring decorator
def monitor_performance(func):
    """Decorator to monitor function performance and log slow operations"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log slow operations
            if execution_time > 2.0:  # Log operations taking more than 2 seconds
                logger.warning(f"Slow operation detected: {func.__name__} took {execution_time:.2f}s")
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in {func.__name__} after {execution_time:.2f}s: {str(e)}")
            raise
    return wrapper

# Database transaction with error handling
def safe_transaction(func):
    """Decorator to handle database transactions safely with retries"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                with transaction.atomic():
                    return func(*args, **kwargs)
            except (DatabaseError, IntegrityError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Database error in {func.__name__}, attempt {attempt + 1}: {str(e)}")
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    logger.error(f"Database error in {func.__name__} after {max_retries} attempts: {str(e)}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                raise
    return wrapper

# AJAX error handler
def ajax_error_handler(func):
    """Decorator for AJAX views to handle errors gracefully"""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except ObjectDoesNotExist as e:
            logger.warning(f"Object not found in {func.__name__}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'آیتم مورد نظر یافت نشد',
                'error_code': 'NOT_FOUND'
            }, status=404)
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'داده‌های ورودی نامعتبر است',
                'error_code': 'VALIDATION_ERROR'
            }, status=400)
        except PermissionError as e:
            logger.warning(f"Permission denied in {func.__name__}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'دسترسی غیرمجاز',
                'error_code': 'PERMISSION_DENIED'
            }, status=403)
        except DatabaseError as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'خطای سیستم داخلی. لطفاً بعداً تلاش کنید',
                'error_code': 'DATABASE_ERROR'
            }, status=500)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'message': 'خطای غیرمنتظره. لطفاً بعداً تلاش کنید',
                'error_code': 'INTERNAL_ERROR'
            }, status=500)
    return wrapper

# View error handler
def view_error_handler(func):
    """Decorator for regular views to handle errors gracefully"""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except ObjectDoesNotExist as e:
            logger.warning(f"Object not found in {func.__name__}: {str(e)}")
            return render(request, 'shop/error.html', {
                'error_message': 'صفحه مورد نظر یافت نشد',
                'error_code': '404'
            }, status=404)
        except PermissionError as e:
            logger.warning(f"Permission denied in {func.__name__}: {str(e)}")
            return render(request, 'shop/error.html', {
                'error_message': 'دسترسی غیرمجاز',
                'error_code': '403'
            }, status=403)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            return render(request, 'shop/error.html', {
                'error_message': 'خطای سیستمی رخ داده است',
                'error_code': '500'
            }, status=500)
    return wrapper

# Cache decorator with error handling
def cached_view(timeout=300, key_prefix='view'):
    """Decorator to cache view results with error handling"""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{request.path}:{request.GET.urlencode()}"
            
            # Try to get from cache
            try:
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache retrieval error for {func.__name__}: {str(e)}")
            
            # Execute function
            result = func(request, *args, **kwargs)
            
            # Cache the result
            try:
                cache.set(cache_key, result, timeout)
            except Exception as e:
                logger.warning(f"Cache storage error for {func.__name__}: {str(e)}")
            
            return result
        return wrapper
    return decorator

# Rate limiting decorator
def rate_limit(requests_per_minute=60):
    """Simple rate limiting decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Get client IP
            client_ip = get_client_ip(request)
            
            # Rate limiting key
            rate_key = f"rate_limit:{func.__name__}:{client_ip}"
            
            try:
                # Check current request count
                current_requests = cache.get(rate_key, 0)
                
                if current_requests >= requests_per_minute:
                    if request.headers.get('Accept') == 'application/json':
                        return JsonResponse({
                            'success': False,
                            'message': 'تعداد درخواست‌ها زیاد است. لطفاً کمی صبر کنید',
                            'error_code': 'RATE_LIMITED'
                        }, status=429)
                    else:
                        return render(request, 'shop/error.html', {
                            'error_message': 'تعداد درخواست‌ها زیاد است',
                            'error_code': '429'
                        }, status=429)
                
                # Increment request count
                cache.set(rate_key, current_requests + 1, 60)  # 1 minute timeout
                
            except Exception as e:
                logger.warning(f"Rate limiting error for {func.__name__}: {str(e)}")
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Enhanced logging context manager
class LoggingContext:
    """Context manager for enhanced logging with performance tracking"""
    
    def __init__(self, operation_name, user=None, extra_data=None):
        self.operation_name = operation_name
        self.user = user
        self.extra_data = extra_data or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"Starting operation: {self.operation_name}", extra={
            'user': str(self.user) if self.user else 'anonymous',
            'operation': self.operation_name,
            **self.extra_data
        })
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - self.start_time
        
        if exc_type is None:
            logger.info(f"Operation completed: {self.operation_name} in {execution_time:.2f}s", extra={
                'user': str(self.user) if self.user else 'anonymous',
                'operation': self.operation_name,
                'execution_time': execution_time,
                'success': True,
                **self.extra_data
            })
        else:
            logger.error(f"Operation failed: {self.operation_name} after {execution_time:.2f}s", extra={
                'user': str(self.user) if self.user else 'anonymous',
                'operation': self.operation_name,
                'execution_time': execution_time,
                'success': False,
                'error': str(exc_val),
                **self.extra_data
            })

# Health check utilities
def check_database_health():
    """Check database connectivity and performance"""
    try:
        from django.db import connection
        start_time = time.time()
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        response_time = time.time() - start_time
        
        return {
            'status': 'healthy',
            'response_time': response_time,
            'message': 'Database connection is working'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'message': 'Database connection failed'
        }

def check_cache_health():
    """Check cache connectivity and performance"""
    try:
        start_time = time.time()
        test_key = f"health_check:{int(time.time())}"
        test_value = "test"
        
        cache.set(test_key, test_value, 10)
        retrieved_value = cache.get(test_key)
        cache.delete(test_key)
        
        response_time = time.time() - start_time
        
        if retrieved_value == test_value:
            return {
                'status': 'healthy',
                'response_time': response_time,
                'message': 'Cache is working'
            }
        else:
            return {
                'status': 'unhealthy',
                'message': 'Cache value mismatch'
            }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'message': 'Cache connection failed'
        }

# Custom exception classes
class BusinessLogicError(Exception):
    """Custom exception for business logic errors"""
    def __init__(self, message, error_code=None):
        super().__init__(message)
        self.error_code = error_code

class ServiceUnavailableError(Exception):
    """Custom exception for service unavailability"""
    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after

# Error reporting utilities
def report_error(error, request=None, extra_context=None):
    """Report errors with comprehensive context"""
    context = {
        'timestamp': timezone.now().isoformat(),
        'error_type': type(error).__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc(),
    }
    
    if request:
        context.update({
            'user': str(request.user) if hasattr(request, 'user') else 'anonymous',
            'path': request.path,
            'method': request.method,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': get_client_ip(request),
        })
    
    if extra_context:
        context.update(extra_context)
    
    logger.error(f"Error Report: {error}", extra=context)
    
    # In production, you might want to send this to an external service
    # like Sentry, Rollbar, or a custom error tracking system

# Performance optimization utilities
def optimize_queryset(queryset, select_related=None, prefetch_related=None):
    """Optimize queryset with select_related and prefetch_related"""
    if select_related:
        queryset = queryset.select_related(*select_related)
    if prefetch_related:
        queryset = queryset.prefetch_related(*prefetch_related)
    return queryset

def batch_database_operations(operations, batch_size=100):
    """Execute database operations in batches for better performance"""
    for i in range(0, len(operations), batch_size):
        batch = operations[i:i + batch_size]
        try:
            with transaction.atomic():
                for operation in batch:
                    operation()
        except Exception as e:
            logger.error(f"Batch operation failed: {str(e)}")
            # You might want to retry individual operations or handle differently
            raise