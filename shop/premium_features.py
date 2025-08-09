"""
Premium Features for High-Class Coffee Shop Experience
"""
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q, Avg, Count, Sum
from django.utils import timezone
from django.core.cache import cache
from .models import *

logger = logging.getLogger(__name__)

class CoffeeRecommendationEngine:
    """
    AI-powered coffee recommendation system
    """
    
    @staticmethod
    def get_personalized_recommendations(user, limit=6):
        """
        Get personalized coffee recommendations based on user behavior
        """
        try:
            # Get user's order history
            user_orders = Order.objects.filter(user=user, status__in=['ready', 'shipping_preparation', 'in_transit', 'pickup_ready'])
            ordered_products = []
            for order in user_orders:
                ordered_products.extend(order.items.all())
            
            # Get user's favorite categories
            favorite_categories = {}
            for item in ordered_products:
                cat = item.product.category
                favorite_categories[cat.id] = favorite_categories.get(cat.id, 0) + item.quantity
            
            # Get products from favorite categories
            if favorite_categories:
                top_categories = sorted(favorite_categories.items(), key=lambda x: x[1], reverse=True)[:3]
                category_ids = [cat_id for cat_id, _ in top_categories]
                
                recommended_products = Product.objects.filter(
                    category_id__in=category_ids
                ).exclude(
                    id__in=[item.product.id for item in ordered_products]
                ).order_by('-featured', '-created_at')[:limit]
            else:
                # For new users, recommend featured products
                recommended_products = Product.objects.filter(
                    featured=True
                ).order_by('-created_at')[:limit]
            
            return recommended_products
        except Exception as e:
            logger.error(f"Error in get_personalized_recommendations: {e}")
            return Product.objects.filter(featured=True)[:limit]

class LoyaltyProgramManager:
    """
    Advanced loyalty program with tier benefits
    """
    
    TIER_BENEFITS = {
        'bronze': {
            'discount_percentage': 0,
            'points_multiplier': 1,
            'free_delivery_threshold': 500000,
            'special_offers': False
        },
        'silver': {
            'discount_percentage': 5,
            'points_multiplier': 1.2,
            'free_delivery_threshold': 300000,
            'special_offers': True
        },
        'gold': {
            'discount_percentage': 10,
            'points_multiplier': 1.5,
            'free_delivery_threshold': 200000,
            'special_offers': True
        },
        'platinum': {
            'discount_percentage': 15,
            'points_multiplier': 2,
            'free_delivery_threshold': 0,
            'special_offers': True
        }
    }
    
    @staticmethod
    def calculate_points_earned(amount):
        """Calculate points earned from purchase amount"""
        return int(amount / 10000)  # 1 point per 10,000 toman
    
    @staticmethod
    def apply_loyalty_discount(user, total_amount):
        """Apply loyalty discount based on user tier"""
        try:
            loyalty = user.loyalty
            tier_benefits = LoyaltyProgramManager.TIER_BENEFITS.get(loyalty.tier, {})
            discount_percentage = tier_benefits.get('discount_percentage', 0)
            
            if discount_percentage > 0:
                discount_amount = total_amount * (discount_percentage / 100)
                return discount_amount, discount_percentage
            
            return 0, 0
        except:
            return 0, 0

class WeatherBasedRecommendations:
    """
    Weather-based drink recommendations
    """
    
    @staticmethod
    def get_weather_recommendations():
        """
        Get recommendations based on current weather
        Note: In production, integrate with weather API
        """
        # Mock weather data - replace with actual weather API
        weather_temp = 25  # Celsius
        
        if weather_temp > 25:
            # Hot weather - recommend cold drinks
            keywords = ['سرد', 'آیس', 'فراپه', 'شیک']
        elif weather_temp < 10:
            # Cold weather - recommend hot drinks
            keywords = ['گرم', 'لاته', 'کاپوچینو', 'چای']
        else:
            # Mild weather - recommend all types
            keywords = ['قهوه', 'نوشیدنی']
        
        # Find products matching weather keywords
        q_objects = Q()
        for keyword in keywords:
            q_objects |= Q(name__icontains=keyword) | Q(description__icontains=keyword)
        
        return Product.objects.filter(q_objects).distinct()[:6]

class InventoryManager:
    """
    Advanced inventory management with low stock alerts
    """
    
    @staticmethod
    def check_low_stock(threshold=10):
        """Check for products with low stock"""
        low_stock_products = Product.objects.filter(stock__lte=threshold)
        
        # Send notifications to admin users
        if low_stock_products.exists():
            admin_users = User.objects.filter(is_staff=True)
            for admin in admin_users:
                for product in low_stock_products:
                    Notification.objects.get_or_create(
                        user=admin,
                        notification_type='low_stock',
                        title='موجودی کم',
                        message=f'موجودی محصول {product.name} به {product.stock} رسیده است.',
                        defaults={'is_read': False}
                    )
        
        return low_stock_products
    
    @staticmethod
    def auto_reorder_suggestions():
        """Generate automatic reorder suggestions based on sales data"""
        # Get sales data from last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        sales_data = OrderItem.objects.filter(
            order__created_at__gte=thirty_days_ago,
            order__status__in=['ready', 'shipping_preparation', 'in_transit', 'pickup_ready']
        ).values('product').annotate(
            total_sold=Sum('quantity')
        ).order_by('-total_sold')
        
        suggestions = []
        for item in sales_data:
            product = Product.objects.get(id=item['product'])
            avg_daily_sales = item['total_sold'] / 30
            recommended_stock = int(avg_daily_sales * 15)  # 15 days stock
            
            if product.stock < recommended_stock:
                suggestions.append({
                    'product': product,
                    'current_stock': product.stock,
                    'recommended_order': recommended_stock - product.stock,
                    'avg_daily_sales': round(avg_daily_sales, 2)
                })
        
        return suggestions

class CustomerInsights:
    """
    Advanced customer analytics and insights
    """
    
    @staticmethod
    def get_customer_segments():
        """Get customer segmentation data"""
        segments = {}
        
        # VIP customers (>5M toman spent)
        segments['vip'] = User.objects.filter(
            loyalty__total_spent__gt=5000000
        ).count()
        
        # Regular customers (500K-5M toman)
        segments['regular'] = User.objects.filter(
            loyalty__total_spent__gte=500000,
            loyalty__total_spent__lte=5000000
        ).count()
        
        # New customers (<500K toman)
        segments['new'] = User.objects.filter(
            loyalty__total_spent__lt=500000
        ).count()
        
        # Inactive customers (no orders in 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        segments['inactive'] = User.objects.filter(
            last_login__lt=thirty_days_ago
        ).count()
        
        return segments
    
    @staticmethod
    def get_peak_hours():
        """Analyze peak ordering hours"""
        cache_key = 'peak_hours_data'
        peak_data = cache.get(cache_key)
        
        if peak_data is None:
            # Analyze orders by hour
            orders = Order.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            )
            
            hour_data = {}
            for hour in range(24):
                hour_orders = orders.filter(created_at__hour=hour).count()
                hour_data[hour] = hour_orders
            
            peak_data = sorted(hour_data.items(), key=lambda x: x[1], reverse=True)[:5]
            cache.set(cache_key, peak_data, 3600)  # Cache for 1 hour
        
        return peak_data

class QualityControlSystem:
    """
    Quality control and feedback analysis system
    """
    
    @staticmethod
    def analyze_feedback_trends():
        """Analyze customer feedback trends"""
        recent_feedback = OrderFeedback.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        analysis = {
            'average_rating': recent_feedback.aggregate(Avg('rating'))['rating__avg'] or 0,
            'total_feedback': recent_feedback.count(),
            'rating_distribution': {},
            'common_complaints': [],
            'top_rated_products': []
        }
        
        # Rating distribution
        for rating in range(1, 6):
            analysis['rating_distribution'][rating] = recent_feedback.filter(
                rating=rating
            ).count()
        
        # Get products with highest average ratings
        top_products = Product.objects.annotate(
            avg_rating=Avg('orderitem__order__feedback__rating')
        ).filter(avg_rating__isnull=False).order_by('-avg_rating')[:5]
        
        analysis['top_rated_products'] = top_products
        
        return analysis

# View functions for premium features

@login_required
def premium_dashboard(request):
    """Premium customer dashboard"""
    context = {
        'recommendations': CoffeeRecommendationEngine.get_personalized_recommendations(request.user),
        'weather_recommendations': WeatherBasedRecommendations.get_weather_recommendations(),
        'loyalty_info': getattr(request.user, 'loyalty', None),
        'recent_orders': Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    }
    return render(request, 'shop/premium_dashboard.html', context)

def business_analytics(request):
    """Advanced business analytics dashboard"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    context = {
        'customer_segments': CustomerInsights.get_customer_segments(),
        'peak_hours': CustomerInsights.get_peak_hours(),
        'inventory_alerts': InventoryManager.check_low_stock(),
        'reorder_suggestions': InventoryManager.auto_reorder_suggestions(),
        'quality_analysis': QualityControlSystem.analyze_feedback_trends()
    }
    
    return render(request, 'shop/business_analytics.html', context)

@login_required
def apply_loyalty_points(request):
    """Apply loyalty points to reduce order total"""
    if request.method == 'POST':
        try:
            points_to_use = int(request.POST.get('points', 0))
            loyalty = request.user.loyalty
            
            if points_to_use > loyalty.points:
                return JsonResponse({
                    'success': False, 
                    'error': 'امتیاز کافی ندارید'
                })
            
            # Each point = 1000 toman discount
            discount_amount = points_to_use * 1000
            
            # Store in session for checkout
            request.session['loyalty_discount'] = {
                'points_used': points_to_use,
                'discount_amount': discount_amount
            }
            
            return JsonResponse({
                'success': True,
                'discount_amount': discount_amount,
                'remaining_points': loyalty.points - points_to_use
            })
            
        except Exception as e:
            logger.error(f"Error applying loyalty points: {e}")
            return JsonResponse({
                'success': False, 
                'error': 'خطا در اعمال امتیاز'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def seasonal_menu(request):
    """Seasonal menu recommendations"""
    import calendar
    current_month = datetime.now().month
    
    # Define seasonal products based on month
    seasonal_keywords = {
        'winter': ['گرم', 'چای', 'شکلات داغ', 'لاته'],  # Dec, Jan, Feb
        'spring': ['نوشیدنی تازه', 'چای سبز', 'دتوکس'],  # Mar, Apr, May
        'summer': ['سرد', 'آیس', 'فراپه', 'شیک'],  # Jun, Jul, Aug
        'autumn': ['قهوه', 'کاپوچینو', 'اسپرسو']  # Sep, Oct, Nov
    }
    
    if current_month in [12, 1, 2]:
        season = 'winter'
    elif current_month in [3, 4, 5]:
        season = 'spring'
    elif current_month in [6, 7, 8]:
        season = 'summer'
    else:
        season = 'autumn'
    
    keywords = seasonal_keywords[season]
    q_objects = Q()
    for keyword in keywords:
        q_objects |= Q(name__icontains=keyword) | Q(description__icontains=keyword)
    
    seasonal_products = Product.objects.filter(q_objects).distinct()
    
    context = {
        'season': season,
        'seasonal_products': seasonal_products,
        'season_name': {
            'winter': 'زمستان',
            'spring': 'بهار', 
            'summer': 'تابستان',
            'autumn': 'پاییز'
        }[season]
    }
    
    return render(request, 'shop/seasonal_menu.html', context)