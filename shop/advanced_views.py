from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.cache import cache
from datetime import datetime, timedelta
import json
import logging
from .models import *
from .ai_recommendation_engine import ai_engine
from .analytics_middleware import track_product_view, track_add_to_cart, track_purchase, track_recommendation_click

logger = logging.getLogger(__name__)

# ===== AI-POWERED RECOMMENDATIONS =====

@login_required
def personalized_recommendations(request):
    """Get personalized product recommendations"""
    try:
        # Get AI recommendations
        recommendations = ai_engine.generate_recommendations(request.user, limit=12)
        
        # Get trending products
        trending_products = ai_engine.get_trending_products(days=7)
        
        # Get collaborative recommendations
        collaborative_recs = ai_engine.get_collaborative_recommendations(request.user, limit=6)
        
        # Get user's saved recommendations
        saved_recommendations = ProductRecommendation.objects.filter(
            user=request.user
        ).select_related('product', 'product__category').order_by('-score')[:6]
        
        context = {
            'recommendations': recommendations,
            'trending_products': trending_products,
            'collaborative_recs': collaborative_recs,
            'saved_recommendations': saved_recommendations,
            'page_title': 'توصیه‌های شخصی‌سازی شده',
            'is_recommendations_page': True
        }
        
        return render(request, 'shop/personalized_recommendations.html', context)
        
    except Exception as e:
        logger.error(f"Error in personalized recommendations: {str(e)}")
        return render(request, 'shop/personalized_recommendations.html', {
            'recommendations': [],
            'error_message': 'خطا در بارگذاری توصیه‌ها'
        })

@login_required
def track_recommendation_view(request, product_id):
    """Track recommendation view for analytics"""
    try:
        product = get_object_or_404(Product, id=product_id)
        recommendation_type = request.GET.get('type', 'ai')
        
        # Track the recommendation click
        track_recommendation_click(request, product, recommendation_type)
        
        # Mark recommendation as viewed
        ProductRecommendation.objects.filter(
            user=request.user,
            product=product
        ).update(is_viewed=True)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error tracking recommendation view: {str(e)}")
        return JsonResponse({'success': False})

# ===== ADVANCED SEARCH & FILTERS =====

def advanced_search(request):
    """Advanced search with sophisticated filters"""
    try:
        # Get search parameters
        query = request.GET.get('q', '')
        category_id = request.GET.get('category', '')
        min_price = request.GET.get('min_price', '')
        max_price = request.GET.get('max_price', '')
        sort_by = request.GET.get('sort', 'relevance')
        availability = request.GET.get('availability', '')
        rating = request.GET.get('rating', '')
        tags = request.GET.getlist('tags')
        
        # Start with all products
        products = Product.objects.filter(is_active=True).select_related('category')
        
        # Apply search query
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query) |
                Q(category__description__icontains=query)
            )
        
        # Apply category filter
        if category_id:
            products = products.filter(category_id=category_id)
        
        # Apply price filters
        if min_price:
            try:
                products = products.filter(price__gte=float(min_price))
            except ValueError:
                pass
        
        if max_price:
            try:
                products = products.filter(price__lte=float(max_price))
            except ValueError:
                pass
        
        # Apply availability filter
        if availability == 'in_stock':
            products = products.filter(stock__gt=0)
        elif availability == 'low_stock':
            products = products.filter(stock__lte=10, stock__gt=0)
        elif availability == 'out_of_stock':
            products = products.filter(stock=0)
        
        # Apply rating filter
        if rating:
            try:
                rating_value = int(rating)
                products = products.annotate(
                    avg_rating=Avg('comments__rating')
                ).filter(avg_rating__gte=rating_value)
            except ValueError:
                pass
        
        # Apply sorting
        if sort_by == 'price_low':
            products = products.order_by('price')
        elif sort_by == 'price_high':
            products = products.order_by('-price')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        elif sort_by == 'popular':
            products = products.annotate(
                like_count=Count('likes'),
                favorite_count=Count('favorites')
            ).order_by('-like_count', '-favorite_count')
        elif sort_by == 'rating':
            products = products.annotate(
                avg_rating=Avg('comments__rating')
            ).order_by('-avg_rating')
        else:  # relevance
            products = products.order_by('name')
        
        # Get categories for filter
        categories = Category.objects.all()
        
        # Get price ranges for filter
        price_ranges = [
            {'min': 0, 'max': 50000, 'label': 'تا ۵۰,۰۰۰ تومان'},
            {'min': 50000, 'max': 100000, 'label': '۵۰,۰۰۰ تا ۱۰۰,۰۰۰ تومان'},
            {'min': 100000, 'max': 200000, 'label': '۱۰۰,۰۰۰ تا ۲۰۰,۰۰۰ تومان'},
            {'min': 200000, 'max': 500000, 'label': '۲۰۰,۰۰۰ تا ۵۰۰,۰۰۰ تومان'},
            {'min': 500000, 'max': None, 'label': 'بیش از ۵۰۰,۰۰۰ تومان'},
        ]
        
        # Pagination
        paginator = Paginator(products, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Track search query
        if query and request.user.is_authenticated:
            SearchQuery.objects.create(
                user=request.user,
                query=query,
                results_count=products.count(),
                filters_applied={
                    'category': category_id,
                    'min_price': min_price,
                    'max_price': max_price,
                    'sort': sort_by,
                    'availability': availability,
                    'rating': rating
                }
            )
        
        context = {
            'products': page_obj,
            'categories': categories,
            'price_ranges': price_ranges,
            'query': query,
            'selected_category': category_id,
            'min_price': min_price,
            'max_price': max_price,
            'sort_by': sort_by,
            'availability': availability,
            'rating': rating,
            'total_results': products.count(),
            'page_title': f'جستجو: {query}' if query else 'جستجو در محصولات'
        }
        
        return render(request, 'shop/advanced_search.html', context)
        
    except Exception as e:
        logger.error(f"Error in advanced search: {str(e)}")
        return render(request, 'shop/advanced_search.html', {
            'products': [],
            'error_message': 'خطا در جستجو'
        })

# ===== REAL-TIME ANALYTICS DASHBOARD =====

@login_required
def analytics_dashboard(request):
    """Real-time analytics dashboard for admins"""
    if not request.user.is_staff:
        return redirect('home')
    
    try:
        # Get real-time metrics
        current_time = timezone.now()
        today = current_time.date()
        yesterday = today - timedelta(days=1)
        this_week = today - timedelta(days=7)
        this_month = today - timedelta(days=30)
        
        # Revenue metrics
        today_revenue = Order.objects.filter(
            created_at__date=today,
            status__in=['delivered', 'shipped']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        yesterday_revenue = Order.objects.filter(
            created_at__date=yesterday,
            status__in=['delivered', 'shipped']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        week_revenue = Order.objects.filter(
            created_at__gte=this_week,
            status__in=['delivered', 'shipped']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        month_revenue = Order.objects.filter(
            created_at__gte=this_month,
            status__in=['delivered', 'shipped']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Order metrics
        today_orders = Order.objects.filter(created_at__date=today).count()
        pending_orders = Order.objects.filter(status='pending').count()
        processing_orders = Order.objects.filter(status='processing').count()
        
        # User metrics
        today_users = User.objects.filter(date_joined__date=today).count()
        active_users = UserActivity.objects.filter(
            timestamp__gte=current_time - timedelta(hours=24)
        ).values('user').distinct().count()
        
        # Product metrics
        total_products = Product.objects.count()
        low_stock_products = Product.objects.filter(stock__lte=10).count()
        out_of_stock_products = Product.objects.filter(stock=0).count()
        
        # Top performing products
        top_products = Product.objects.annotate(
            total_sold=Sum('orderitem__quantity'),
            total_revenue=Sum(F('orderitem__quantity') * F('orderitem__price'))
        ).filter(total_sold__gt=0).order_by('-total_revenue')[:5]
        
        # Recent orders
        recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
        
        # Customer segments
        segment_stats = CustomerSegment.objects.values('segment_type').annotate(
            count=Count('id'),
            total_spent=Sum('total_spent')
        ).order_by('-total_spent')
        
        # Search analytics
        popular_searches = SearchQuery.objects.filter(
            timestamp__gte=this_week
        ).values('query').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Real-time metrics from cache
        active_users_count = cache.get('active_users_count', 0)
        current_minute = current_time.strftime('%Y-%m-%d %H:%M')
        page_views_this_minute = cache.get(f'page_views_{current_minute}', 0)
        
        context = {
            'today_revenue': today_revenue,
            'yesterday_revenue': yesterday_revenue,
            'week_revenue': week_revenue,
            'month_revenue': month_revenue,
            'today_orders': today_orders,
            'pending_orders': pending_orders,
            'processing_orders': processing_orders,
            'today_users': today_users,
            'active_users': active_users,
            'total_products': total_products,
            'low_stock_products': low_stock_products,
            'out_of_stock_products': out_of_stock_products,
            'top_products': top_products,
            'recent_orders': recent_orders,
            'segment_stats': segment_stats,
            'popular_searches': popular_searches,
            'active_users_count': active_users_count,
            'page_views_this_minute': page_views_this_minute,
            'revenue_growth': ((today_revenue - yesterday_revenue) / yesterday_revenue * 100) if yesterday_revenue > 0 else 0,
            'page_title': 'داشبورد تحلیلات'
        }
        
        return render(request, 'shop/analytics_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in analytics dashboard: {str(e)}")
        return render(request, 'shop/analytics_dashboard.html', {
            'error_message': 'خطا در بارگذاری داشبورد'
        })

# ===== ENHANCED PRODUCT VIEWS =====

def enhanced_product_detail(request, product_id):
    """Enhanced product detail with AI recommendations"""
    try:
        product = get_object_or_404(Product, id=product_id)
        
        # Track product view
        if request.user.is_authenticated:
            track_product_view(request, product)
        
        # Get product reviews with ratings
        reviews = Comment.objects.filter(product=product).select_related('user').order_by('-created_at')
        
        # Calculate average rating
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        
        # Get related products using AI
        if request.user.is_authenticated:
            related_products = ai_engine.generate_recommendations(request.user, limit=4)
        else:
            # Fallback to category-based recommendations
            related_products = Product.objects.filter(
                category=product.category
            ).exclude(id=product.id)[:4]
        
        # Get user's interaction status
        user_liked = False
        user_favorited = False
        if request.user.is_authenticated:
            user_liked = ProductLike.objects.filter(product=product, user=request.user).exists()
            user_favorited = ProductFavorite.objects.filter(product=product, user=request.user).exists()
        
        # Get product statistics
        like_count = ProductLike.objects.filter(product=product).count()
        favorite_count = ProductFavorite.objects.filter(product=product).count()
        review_count = reviews.count()
        
        # Get product variants (if any)
        product_variants = Product.objects.filter(
            name__startswith=product.name.split(' - ')[0]
        ).exclude(id=product.id)[:3]
        
        context = {
            'product': product,
            'reviews': reviews,
            'avg_rating': avg_rating,
            'related_products': related_products,
            'user_liked': user_liked,
            'user_favorited': user_favorited,
            'like_count': like_count,
            'favorite_count': favorite_count,
            'review_count': review_count,
            'product_variants': product_variants,
            'page_title': product.name
        }
        
        return render(request, 'shop/enhanced_product_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error in enhanced product detail: {str(e)}")
        return redirect('product_detail', product_id=product_id)

# ===== LOYALTY PROGRAM =====

@login_required
def loyalty_dashboard(request):
    """User loyalty program dashboard"""
    try:
        # Get or create loyalty account
        loyalty, created = LoyaltyProgram.objects.get_or_create(user=request.user)
        
        # Calculate points from recent orders
        recent_orders = Order.objects.filter(
            user=request.user,
            status__in=['delivered', 'shipped'],
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        # Calculate points earned (1 point per 1000 toman)
        points_earned = sum(order.total_amount / 1000 for order in recent_orders)
        
        # Update loyalty account
        if points_earned > 0:
            loyalty.add_points(int(points_earned))
        
        # Get available rewards
        available_rewards = [
            {'points': 100, 'reward': '۱۰٪ تخفیف', 'description': 'تخفیف ۱۰٪ روی سفارش بعدی'},
            {'points': 200, 'reward': '۲۰٪ تخفیف', 'description': 'تخفیف ۲۰٪ روی سفارش بعدی'},
            {'points': 500, 'reward': 'قهوه رایگان', 'description': 'یک قهوه رایگان'},
            {'points': 1000, 'reward': 'دسر رایگان', 'description': 'یک دسر رایگان'},
        ]
        
        # Get user's tier benefits
        tier_benefits = {
            'bronze': ['تخفیف ۵٪ روی سفارشات بالای ۲۰۰,۰۰۰ تومان'],
            'silver': ['تخفیف ۱۰٪ روی سفارشات بالای ۱۵۰,۰۰۰ تومان', 'ارسال رایگان'],
            'gold': ['تخفیف ۱۵٪ روی سفارشات بالای ۱۰۰,۰۰۰ تومان', 'ارسال رایگان', 'اولویت در سفارشات'],
            'platinum': ['تخفیف ۲۰٪ روی همه سفارشات', 'ارسال رایگان', 'اولویت در سفارشات', 'خدمات ویژه']
        }
        
        context = {
            'loyalty': loyalty,
            'available_rewards': available_rewards,
            'tier_benefits': tier_benefits.get(loyalty.tier, []),
            'recent_orders': recent_orders,
            'points_earned': int(points_earned),
            'page_title': 'برنامه وفاداری'
        }
        
        return render(request, 'shop/loyalty_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in loyalty dashboard: {str(e)}")
        return render(request, 'shop/loyalty_dashboard.html', {
            'error_message': 'خطا در بارگذاری برنامه وفاداری'
        })

@login_required
def redeem_points(request):
    """Redeem loyalty points"""
    try:
        data = json.loads(request.body)
        points_to_redeem = int(data.get('points', 0))
        
        loyalty = LoyaltyProgram.objects.get(user=request.user)
        
        if loyalty.points >= points_to_redeem:
            success = loyalty.redeem_points(points_to_redeem)
            if success:
                return JsonResponse({
                    'success': True,
                    'message': f'{points_to_redeem} امتیاز با موفقیت استفاده شد',
                    'remaining_points': loyalty.points
                })
        
        return JsonResponse({
            'success': False,
            'message': 'امتیاز کافی نیست'
        })
        
    except Exception as e:
        logger.error(f"Error redeeming points: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'خطا در استفاده از امتیاز'
        })

# ===== CUSTOMER SEGMENTATION =====

@login_required
def customer_insights(request):
    """Customer insights and segmentation"""
    if not request.user.is_staff:
        return redirect('home')
    
    try:
        # Get customer segments
        segments = CustomerSegment.objects.select_related('user').all()
        
        # Segment statistics
        segment_stats = {}
        for segment in segments:
            segment_type = segment.get_segment_type_display()
            if segment_type not in segment_stats:
                segment_stats[segment_type] = {
                    'count': 0,
                    'total_spent': 0,
                    'avg_order_value': 0
                }
            
            segment_stats[segment_type]['count'] += 1
            segment_stats[segment_type]['total_spent'] += float(segment.total_spent)
        
        # Calculate averages
        for stats in segment_stats.values():
            if stats['count'] > 0:
                stats['avg_order_value'] = stats['total_spent'] / stats['count']
        
        # Get top customers
        top_customers = CustomerSegment.objects.select_related('user').order_by('-total_spent')[:10]
        
        # Get customer behavior patterns
        behavior_patterns = UserActivity.objects.values('action').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        context = {
            'segments': segments,
            'segment_stats': segment_stats,
            'top_customers': top_customers,
            'behavior_patterns': behavior_patterns,
            'page_title': 'تحلیل مشتریان'
        }
        
        return render(request, 'shop/customer_insights.html', context)
        
    except Exception as e:
        logger.error(f"Error in customer insights: {str(e)}")
        return render(request, 'shop/customer_insights.html', {
            'error_message': 'خطا در بارگذاری تحلیل مشتریان'
        })

# ===== API ENDPOINTS =====

@login_required
def api_recommendations(request):
    """API endpoint for recommendations"""
    try:
        limit = int(request.GET.get('limit', 6))
        recommendations = ai_engine.generate_recommendations(request.user, limit=limit)
        
        data = []
        for product in recommendations:
            data.append({
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'image': product.image.url if product.image else None,
                'category': product.category.name,
                'url': f'/product/{product.id}/'
            })
        
        return JsonResponse({'recommendations': data})
        
    except Exception as e:
        logger.error(f"Error in API recommendations: {str(e)}")
        return JsonResponse({'error': 'خطا در بارگذاری توصیه‌ها'}, status=500)

@login_required
def api_analytics(request):
    """API endpoint for user analytics"""
    try:
        # Get user's recent activity
        recent_activities = UserActivity.objects.filter(
            user=request.user
        ).select_related('product', 'category').order_by('-timestamp')[:10]
        
        # Get user's segment
        segment = CustomerSegment.objects.filter(user=request.user).first()
        
        # Get loyalty info
        loyalty = LoyaltyProgram.objects.filter(user=request.user).first()
        
        data = {
            'recent_activities': [
                {
                    'action': activity.action,
                    'page': activity.page,
                    'timestamp': activity.timestamp.isoformat(),
                    'product_name': activity.product.name if activity.product else None,
                    'category_name': activity.category.name if activity.category else None
                }
                for activity in recent_activities
            ],
            'segment': segment.get_segment_type_display() if segment else 'جدید',
            'loyalty_points': loyalty.points if loyalty else 0,
            'loyalty_tier': loyalty.tier if loyalty else 'bronze'
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error in API analytics: {str(e)}")
        return JsonResponse({'error': 'خطا در بارگذاری اطلاعات'}, status=500) 