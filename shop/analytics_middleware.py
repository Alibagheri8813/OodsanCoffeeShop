import time
import json
import logging
from django.utils import timezone
from django.http import JsonResponse
from django.core.cache import cache
from django.db import transaction
from django.contrib.auth.models import AnonymousUser
from .models import UserActivity, AnalyticsEvent, SearchQuery
from .ai_recommendation_engine import ai_engine

logger = logging.getLogger(__name__)

class AnalyticsMiddleware:
    """Advanced analytics middleware for tracking user behavior"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.start_time = None
    
    def __call__(self, request):
        # Start timing
        self.start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Track analytics after response
        self.track_analytics(request, response)
        
        return response
    
    def track_analytics(self, request, response):
        """Track comprehensive analytics data"""
        try:
            # Skip tracking for certain paths
            if self.should_skip_tracking(request.path):
                return
            
            # Calculate session duration
            session_duration = int((time.time() - self.start_time) * 1000) if self.start_time else 0
            
            # Get user and session info
            user = request.user if hasattr(request, 'user') else AnonymousUser()
            session_id = request.session.session_key or 'anonymous'
            
            # Detect device type
            device_type = self.detect_device_type(request)
            
            # Track page view
            if user.is_authenticated:
                self.track_user_activity(
                    user=user,
                    page=request.path,
                    action='page_view',
                    session_duration=session_duration,
                    device_type=device_type,
                    request=request
                )
            
            # Track analytics event
            self.track_analytics_event(
                event_type='page_view',
                user=user if user.is_authenticated else None,
                session_id=session_id,
                metadata={
                    'path': request.path,
                    'method': request.method,
                    'device_type': device_type,
                    'session_duration': session_duration,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'referrer': request.META.get('HTTP_REFERER', ''),
                    'ip_address': self.get_client_ip(request)
                }
            )
            
            # Track search queries
            if 'search' in request.path or 'q=' in request.GET:
                self.track_search_query(request, user)
            
            # Update user segment for authenticated users
            if user.is_authenticated:
                self.update_user_analytics(user)
                
        except Exception as e:
            logger.error(f"Error tracking analytics: {str(e)}")
    
    def should_skip_tracking(self, path):
        """Check if path should be skipped for tracking"""
        skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/robots.txt',
            '/sitemap.xml',
            '/api/',
        ]
        
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def detect_device_type(self, request):
        """Detect device type from user agent"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            return 'mobile'
        elif 'tablet' in user_agent or 'ipad' in user_agent:
            return 'tablet'
        else:
            return 'desktop'
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def track_user_activity(self, user, page, action, session_duration=0, device_type='desktop', request=None):
        """Track user activity for AI recommendations"""
        try:
            # Extract product and category from URL
            product = None
            category = None
            
            if 'product/' in page:
                try:
                    product_id = page.split('product/')[1].split('/')[0]
                    product = Product.objects.get(id=product_id)
                    category = product.category
                except (ValueError, Product.DoesNotExist):
                    pass
            elif 'category/' in page:
                try:
                    category_id = page.split('category/')[1].split('/')[0]
                    category = Category.objects.get(id=category_id)
                except (ValueError, Category.DoesNotExist):
                    pass
            
            # Create user activity
            UserActivity.objects.create(
                user=user,
                page=page,
                action=action,
                product=product,
                category=category,
                session_duration=session_duration,
                device_type=device_type
            )
            
        except Exception as e:
            logger.error(f"Error tracking user activity: {str(e)}")
    
    def track_analytics_event(self, event_type, user=None, product=None, category=None, 
                            order=None, session_id=None, metadata=None):
        """Track analytics event"""
        try:
            AnalyticsEvent.objects.create(
                event_type=event_type,
                user=user,
                product=product,
                category=category,
                order=order,
                session_id=session_id or 'anonymous',
                metadata=metadata or {},
                ip_address=metadata.get('ip_address') if metadata else None
            )
            
        except Exception as e:
            logger.error(f"Error tracking analytics event: {str(e)}")
    
    def track_search_query(self, request, user):
        """Track search queries for analytics"""
        try:
            query = request.GET.get('q', '')
            if not query:
                return
            
            # Count results
            results_count = 0
            if hasattr(request, 'resolver_match') and request.resolver_match:
                view_func = request.resolver_match.func
                if hasattr(view_func, '__name__') and 'search' in view_func.__name__.lower():
                    # This is a search view, we can estimate results
                    results_count = 10  # Default estimate
            
            # Get applied filters
            filters_applied = {}
            filter_params = ['category', 'min_price', 'max_price', 'sort']
            for param in filter_params:
                value = request.GET.get(param)
                if value:
                    filters_applied[param] = value
            
            # Create search query record
            SearchQuery.objects.create(
                user=user if user.is_authenticated else None,
                query=query,
                results_count=results_count,
                filters_applied=filters_applied,
                session_id=request.session.session_key or 'anonymous'
            )
            
        except Exception as e:
            logger.error(f"Error tracking search query: {str(e)}")
    
    def update_user_analytics(self, user):
        """Update user analytics and segments"""
        try:
            # Update user segment in background
            ai_engine.update_user_segment(user)
            
            # Cache user analytics for performance
            cache_key = f"user_analytics_{user.id}"
            cache.set(cache_key, {
                'last_activity': timezone.now(),
                'segment_updated': True
            }, timeout=3600)  # 1 hour cache
            
        except Exception as e:
            logger.error(f"Error updating user analytics: {str(e)}")

class RealTimeAnalyticsMiddleware:
    """Real-time analytics for live dashboard"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Track real-time metrics
        self.track_real_time_metrics(request)
        
        return response
    
    def track_real_time_metrics(self, request):
        """Track real-time business metrics"""
        try:
            # Update active users count
            cache_key = 'active_users_count'
            active_users = cache.get(cache_key, 0)
            cache.set(cache_key, active_users + 1, timeout=300)  # 5 minutes
            
            # Track page views per minute
            current_minute = timezone.now().strftime('%Y-%m-%d %H:%M')
            page_views_key = f'page_views_{current_minute}'
            page_views = cache.get(page_views_key, 0)
            cache.set(page_views_key, page_views + 1, timeout=120)  # 2 minutes
            
            # Track unique visitors
            if request.user.is_authenticated:
                unique_visitors_key = f'unique_visitors_{current_minute}'
                unique_visitors = cache.get(unique_visitors_key, set())
                unique_visitors.add(request.user.id)
                cache.set(unique_visitors_key, unique_visitors, timeout=120)
            
        except Exception as e:
            logger.error(f"Error tracking real-time metrics: {str(e)}")

class PerformanceMonitoringMiddleware:
    """Monitor application performance"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Track slow requests
        if response_time > 1.0:  # More than 1 second
            logger.warning(f"Slow request: {request.path} took {response_time:.2f}s")
        
        # Add performance headers
        response['X-Response-Time'] = f"{response_time:.3f}s"
        
        return response

# Analytics tracking functions for views
def track_product_view(request, product):
    """Track product view for analytics"""
    try:
        if request.user.is_authenticated:
            # Track user activity
            UserActivity.objects.create(
                user=request.user,
                page=f'/product/{product.id}/',
                action='product_view',
                product=product,
                category=product.category
            )
            
            # Track analytics event
            AnalyticsEvent.objects.create(
                event_type='product_view',
                user=request.user,
                product=product,
                category=product.category,
                metadata={
                    'product_name': product.name,
                    'product_price': float(product.price),
                    'product_category': product.category.name
                }
            )
            
    except Exception as e:
        logger.error(f"Error tracking product view: {str(e)}")

def track_add_to_cart(request, product, quantity):
    """Track add to cart event"""
    try:
        if request.user.is_authenticated:
            AnalyticsEvent.objects.create(
                event_type='add_to_cart',
                user=request.user,
                product=product,
                category=product.category,
                metadata={
                    'quantity': quantity,
                    'product_name': product.name,
                    'product_price': float(product.price),
                    'total_value': float(product.price * quantity)
                }
            )
            
    except Exception as e:
        logger.error(f"Error tracking add to cart: {str(e)}")

def track_purchase(request, order):
    """Track purchase event"""
    try:
        if request.user.is_authenticated:
            AnalyticsEvent.objects.create(
                event_type='purchase',
                user=request.user,
                order=order,
                metadata={
                    'order_id': order.id,
                    'total_amount': float(order.total_amount),
                    'item_count': order.items.count(),
                    'delivery_method': order.delivery_method
                }
            )
            
    except Exception as e:
        logger.error(f"Error tracking purchase: {str(e)}")

def track_recommendation_click(request, product, recommendation_type):
    """Track recommendation click"""
    try:
        if request.user.is_authenticated:
            AnalyticsEvent.objects.create(
                event_type='recommendation_click',
                user=request.user,
                product=product,
                category=product.category,
                metadata={
                    'recommendation_type': recommendation_type,
                    'product_name': product.name
                }
            )
            
    except Exception as e:
        logger.error(f"Error tracking recommendation click: {str(e)}") 