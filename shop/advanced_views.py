"""
Advanced Views for Phase 3 Features
Includes: AI Recommendations, Analytics Dashboard, Advanced Search, Loyalty Program
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg, F, Max, Min
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.cache import cache
from datetime import datetime, timedelta
import json
import logging
from decimal import Decimal

from .models import *
from .ai_recommendation_engine import ai_engine
from .error_handling import monitor_performance, safe_transaction, ajax_error_handler

logger = logging.getLogger(__name__)

# ===== AI RECOMMENDATIONS =====

@login_required
@monitor_performance
def personalized_recommendations(request):
    """Personalized AI recommendations page"""
    try:
        # Generate AI recommendations
        recommendations_data = ai_engine.generate_recommendations(request.user, limit=12)
        
        # Get actual product objects
        recommendations = []
        for rec_data in recommendations_data:
            try:
                product = Product.objects.get(id=rec_data['product_id'], stock__gt=0)
                recommendations.append({
                    'product': product,
                    'score': rec_data['similarity_score'],
                    'reason': rec_data['reason']
                })
            except Product.DoesNotExist:
                continue
        
        # Get user's recommendation stats
        stats = ai_engine.get_user_recommendation_stats(request.user)
        
        # Get trending products for additional recommendations
        trending = ai_engine.get_trending_products(days=7, limit=6)
        trending_products = []
        for trend_data in trending:
            try:
                product = Product.objects.get(id=trend_data['product_id'], stock__gt=0)
                trending_products.append(product)
            except Product.DoesNotExist:
                continue
        
        context = {
            'recommendations': recommendations,
            'trending_products': trending_products,
            'stats': stats,
            'page_title': 'پیشنهادات هوشمند'
        }
        
        return render(request, 'shop/recommendations.html', context)
        
    except Exception as e:
        logger.error(f"Error in personalized recommendations: {e}")
        messages.error(request, 'خطا در بارگیری پیشنهادات')
        return redirect('shop_home')

@login_required
@require_POST
def track_recommendation_view(request, product_id):
    """Track when user views a recommended product"""
    try:
        ai_engine.track_recommendation_interaction(request.user, product_id, 'view')
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f"Error tracking recommendation view: {e}")
        return JsonResponse({'status': 'error'})

# ===== ANALYTICS DASHBOARD =====

@user_passes_test(lambda u: u.is_staff)
@monitor_performance
def analytics_dashboard(request):
    """Real-time analytics dashboard for admins"""
    try:
        # Get date range
        days = int(request.GET.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Revenue Analytics
        revenue_data = Order.objects.filter(
            created_at__gte=start_date,
            status__in=['paid', 'processing', 'shipped', 'delivered']
        ).aggregate(
            total_revenue=Sum('total_amount'),
            order_count=Count('id'),
            avg_order_value=Avg('total_amount')
        )
        
        # Previous period for comparison
        prev_start = start_date - timedelta(days=days)
        prev_revenue_data = Order.objects.filter(
            created_at__gte=prev_start,
            created_at__lt=start_date,
            status__in=['paid', 'processing', 'shipped', 'delivered']
        ).aggregate(
            total_revenue=Sum('total_amount'),
            order_count=Count('id')
        )
        
        # Calculate growth rates
        current_revenue = revenue_data['total_revenue'] or 0
        prev_revenue = prev_revenue_data['total_revenue'] or 0
        revenue_growth = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        
        current_orders = revenue_data['order_count'] or 0
        prev_orders = prev_revenue_data['order_count'] or 0
        order_growth = ((current_orders - prev_orders) / prev_orders * 100) if prev_orders > 0 else 0
        
        # Top Products
        top_products = Product.objects.filter(
            orderitem__order__created_at__gte=start_date,
            orderitem__order__status__in=['paid', 'processing', 'shipped', 'delivered']
        ).annotate(
            total_sold=Sum('orderitem__quantity'),
            total_revenue=Sum(F('orderitem__quantity') * F('orderitem__price'))
        ).filter(total_sold__gt=0).order_by('-total_revenue')[:10]
        
        # User Analytics
        user_stats = {
            'total_users': User.objects.count(),
            'new_users': User.objects.filter(date_joined__gte=start_date).count(),
            'active_users': UserActivity.objects.filter(
                timestamp__gte=start_date
            ).values('user').distinct().count()
        }
        
        # Customer Segments
        segments = CustomerSegment.objects.values('segment_type').annotate(
            count=Count('id'),
            total_spent=Sum('total_spent')
        ).order_by('-total_spent')
        
        # Low Stock Alerts
        low_stock_products = Product.objects.filter(
            stock__lte=10,
            stock__gt=0
        ).order_by('stock')
        
        out_of_stock = Product.objects.filter(stock=0).count()
        
        # Search Analytics
        popular_searches = SearchQuery.objects.filter(
            timestamp__gte=start_date
        ).values('query').annotate(
            search_count=Count('id'),
            avg_results=Avg('results_count')
        ).order_by('-search_count')[:10]
        
        # Daily revenue chart data
        daily_revenue = []
        current_date = start_date.date()
        while current_date <= end_date.date():
            day_revenue = Order.objects.filter(
                created_at__date=current_date,
                status__in=['paid', 'processing', 'shipped', 'delivered']
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            daily_revenue.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'revenue': float(day_revenue)
            })
            current_date += timedelta(days=1)
        
        context = {
            'revenue_data': revenue_data,
            'revenue_growth': revenue_growth,
            'order_growth': order_growth,
            'top_products': top_products,
            'user_stats': user_stats,
            'segments': segments,
            'low_stock_products': low_stock_products,
            'out_of_stock_count': out_of_stock,
            'popular_searches': popular_searches,
            'daily_revenue': json.dumps(daily_revenue),
            'days': days,
            'page_title': 'داشبورد تحلیلات'
        }
        
        return render(request, 'shop/analytics_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in analytics dashboard: {e}")
        messages.error(request, 'خطا در بارگیری داشبورد تحلیلات')
        return redirect('admin_dashboard')

@user_passes_test(lambda u: u.is_staff)
def customer_insights(request):
    """Customer segmentation and insights"""
    try:
        # Customer segments with detailed analysis
        segments = CustomerSegment.objects.select_related('user').annotate(
            orders_count=Count('user__orders'),
            last_activity=Max('user__activities__timestamp')
        ).order_by('-total_spent')
        
        # Segment statistics
        segment_stats = CustomerSegment.objects.values('segment_type').annotate(
            count=Count('id'),
            avg_spent=Avg('total_spent'),
            total_revenue=Sum('total_spent'),
            avg_orders=Avg('order_count')
        ).order_by('-total_revenue')
        
        # Loyalty tier distribution
        loyalty_stats = LoyaltyProgram.objects.values('tier').annotate(
            count=Count('id'),
            total_points=Sum('points')
        ).order_by('-count')
        
        # Recent user activities
        recent_activities = UserActivity.objects.select_related(
            'user', 'product', 'category'
        ).order_by('-timestamp')[:50]
        
        # Top customers
        top_customers = CustomerSegment.objects.select_related('user').order_by('-total_spent')[:20]
        
        # Inactive customers (no activity in 30 days)
        inactive_threshold = timezone.now() - timedelta(days=30)
        inactive_customers = User.objects.filter(
            last_login__lt=inactive_threshold
        ).exclude(
            activities__timestamp__gte=inactive_threshold
        ).count()
        
        context = {
            'segments': segments,
            'segment_stats': segment_stats,
            'loyalty_stats': loyalty_stats,
            'recent_activities': recent_activities,
            'top_customers': top_customers,
            'inactive_customers': inactive_customers,
            'page_title': 'تحلیل مشتریان'
        }
        
        return render(request, 'shop/customer_insights.html', context)
        
    except Exception as e:
        logger.error(f"Error in customer insights: {e}")
        messages.error(request, 'خطا در بارگیری تحلیل مشتریان')
        return redirect('analytics_dashboard')

# ===== ADVANCED SEARCH =====

@monitor_performance
def advanced_search(request):
    """Advanced search with multiple filters"""
    try:
        query = request.GET.get('q', '').strip()
        category_id = request.GET.get('category')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        availability = request.GET.get('availability')
        rating = request.GET.get('rating')
        sort_by = request.GET.get('sort', 'relevance')
        
        # Start with all active products
        products = Product.objects.filter(stock__gte=0)
        
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
                products = products.filter(price__gte=Decimal(min_price))
            except (ValueError, TypeError):
                pass
        
        if max_price:
            try:
                products = products.filter(price__lte=Decimal(max_price))
            except (ValueError, TypeError):
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
                rating_value = float(rating)
                products = products.annotate(
                    avg_rating=Avg('comments__rating')
                ).filter(avg_rating__gte=rating_value)
            except (ValueError, TypeError):
                pass
        
        # Apply sorting
        if sort_by == 'price_low':
            products = products.order_by('price')
        elif sort_by == 'price_high':
            products = products.order_by('-price')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        elif sort_by == 'popularity':
            products = products.annotate(
                like_count=Count('productinteraction', filter=Q(productinteraction__interaction_type='like'))
            ).order_by('-like_count', '-created_at')
        elif sort_by == 'rating':
            products = products.annotate(
                avg_rating=Avg('comments__rating')
            ).order_by('-avg_rating', '-created_at')
        else:  # relevance
            products = products.order_by('-featured', '-created_at')
        
        # Track search query
        if request.user.is_authenticated and query:
            SearchQuery.objects.create(
                user=request.user,
                query=query,
                results_count=products.count(),
                filters_used={
                    'category': category_id,
                    'min_price': min_price,
                    'max_price': max_price,
                    'availability': availability,
                    'rating': rating,
                    'sort': sort_by
                }
            )
        
        # Pagination
        paginator = Paginator(products, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get categories for filter
        categories = Category.objects.filter(parent__isnull=True)
        
        # Get price range for filter
        price_range = Product.objects.filter(stock__gt=0).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        
        context = {
            'page_obj': page_obj,
            'products': page_obj.object_list,
            'categories': categories,
            'price_range': price_range,
            'search_params': {
                'q': query,
                'category': category_id,
                'min_price': min_price,
                'max_price': max_price,
                'availability': availability,
                'rating': rating,
                'sort': sort_by
            },
            'total_results': paginator.count,
            'page_title': f'جستجو: {query}' if query else 'جستجوی پیشرفته'
        }
        
        return render(request, 'shop/advanced_search.html', context)
        
    except Exception as e:
        logger.error(f"Error in advanced search: {e}")
        messages.error(request, 'خطا در جستجو')
        return redirect('shop_home')

# ===== ENHANCED PRODUCT DETAIL =====

@monitor_performance
def enhanced_product_detail(request, product_id):
    """Enhanced product detail page with AI recommendations"""
    try:
        product = get_object_or_404(Product, id=product_id, stock__gte=0)
        
        # Track product view
        if request.user.is_authenticated:
            UserActivity.objects.create(
                user=request.user,
                page=f'/enhanced-product/{product_id}/',
                action='view',
                product=product,
                category=product.category
            )
            
            ProductInteraction.objects.create(
                user=request.user,
                product=product,
                interaction_type='view'
            )
        
        # Get similar products using AI
        similar_products_data = ai_engine.get_product_similarities(product_id, limit=6)
        similar_products = []
        for sim_data in similar_products_data:
            try:
                sim_product = Product.objects.get(id=sim_data['product_id'], stock__gt=0)
                similar_products.append(sim_product)
            except Product.DoesNotExist:
                continue
        
        # Get product statistics
        product_stats = {
            'view_count': ProductInteraction.objects.filter(
                product=product, 
                interaction_type='view'
            ).count(),
            'like_count': ProductInteraction.objects.filter(
                product=product, 
                interaction_type='like'
            ).count(),
            'favorite_count': ProductInteraction.objects.filter(
                product=product, 
                interaction_type='favorite'
            ).count(),
            'purchase_count': OrderItem.objects.filter(product=product).aggregate(
                total=Sum('quantity')
            )['total'] or 0
        }
        
        # Get product reviews with ratings
        reviews = Comment.objects.filter(
            product=product, 
            is_approved=True
        ).select_related('user').order_by('-created_at')
        
        # Calculate average rating
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        rating_distribution = reviews.values('rating').annotate(
            count=Count('id')
        ).order_by('rating')
        
        # Check if user has interacted with this product
        user_interactions = {}
        if request.user.is_authenticated:
            interactions = ProductInteraction.objects.filter(
                user=request.user, 
                product=product
            ).values_list('interaction_type', flat=True)
            user_interactions = {interaction: True for interaction in interactions}
        
        # Get trending products in same category
        trending_in_category = ai_engine.get_trending_products(days=7, limit=4)
        trending_products = []
        for trend_data in trending_in_category:
            try:
                trend_product = Product.objects.get(
                    id=trend_data['product_id'], 
                    category=product.category,
                    stock__gt=0
                )
                trending_products.append(trend_product)
            except Product.DoesNotExist:
                continue
        
        context = {
            'product': product,
            'similar_products': similar_products,
            'product_stats': product_stats,
            'reviews': reviews,
            'avg_rating': avg_rating,
            'rating_distribution': rating_distribution,
            'user_interactions': user_interactions,
            'trending_products': trending_products,
            'page_title': product.name
        }
        
        return render(request, 'shop/enhanced_product_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error in enhanced product detail: {e}")
        messages.error(request, 'خطا در بارگیری محصول')
        return redirect('shop_home')

# ===== LOYALTY PROGRAM =====

@login_required
@monitor_performance
def loyalty_dashboard(request):
    """Loyalty program dashboard"""
    try:
        # Get or create loyalty program for user
        loyalty, created = LoyaltyProgram.objects.get_or_create(
            user=request.user,
            defaults={'points': 0, 'tier': 'bronze'}
        )
        
        # Get or create customer segment
        segment, seg_created = CustomerSegment.objects.get_or_create(
            user=request.user,
            defaults={'segment_type': 'new'}
        )
        
        # Update tier based on spending
        new_tier = loyalty.calculate_tier()
        if new_tier != loyalty.tier:
            loyalty.tier = new_tier
            loyalty.tier_achieved_date = timezone.now()
            loyalty.save()
        
        # Get tier benefits
        benefits = loyalty.get_tier_benefits()
        
        # Calculate points from recent orders
        recent_orders = Order.objects.filter(
            user=request.user,
            status__in=['paid', 'processing', 'shipped', 'delivered'],
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        recent_points_earned = sum(
            int(order.total_amount / 1000) for order in recent_orders
        )
        
        # Get points history (simplified)
        points_history = []
        for order in recent_orders:
            points_earned = int(order.total_amount / 1000)
            points_history.append({
                'date': order.created_at,
                'points': points_earned,
                'description': f'خرید سفارش #{order.id}',
                'type': 'earned'
            })
        
        # Available rewards (simplified)
        available_rewards = [
            {'name': 'تخفیف 50 هزار تومانی', 'points_required': 50, 'discount': 50000},
            {'name': 'تخفیف 100 هزار تومانی', 'points_required': 100, 'discount': 100000},
            {'name': 'تخفیف 200 هزار تومانی', 'points_required': 200, 'discount': 200000},
            {'name': 'ارسال رایگان', 'points_required': 30, 'benefit': 'free_shipping'},
            {'name': 'قهوه رایگان', 'points_required': 150, 'benefit': 'free_coffee'},
        ]
        
        # Points needed for next tier
        tier_thresholds = {
            'bronze': 0,
            'silver': 500,
            'gold': 2000,
            'platinum': 5000
        }
        
        current_tier_points = tier_thresholds.get(loyalty.tier, 0)
        tiers = ['bronze', 'silver', 'gold', 'platinum']
        current_tier_index = tiers.index(loyalty.tier)
        
        next_tier_points = 0
        if current_tier_index < len(tiers) - 1:
            next_tier = tiers[current_tier_index + 1]
            next_tier_points = tier_thresholds[next_tier] - segment.total_spent / 1000
        
        context = {
            'loyalty': loyalty,
            'segment': segment,
            'benefits': benefits,
            'points_history': points_history,
            'available_rewards': available_rewards,
            'recent_points_earned': recent_points_earned,
            'next_tier_points': max(0, next_tier_points),
            'progress_percentage': min(100, (segment.total_spent / 1000) / tier_thresholds.get(
                tiers[min(current_tier_index + 1, len(tiers) - 1)], 5000
            ) * 100) if current_tier_index < len(tiers) - 1 else 100,
            'page_title': 'برنامه وفاداری'
        }
        
        return render(request, 'shop/loyalty_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in loyalty dashboard: {e}")
        messages.error(request, 'خطا در بارگیری برنامه وفاداری')
        return redirect('user_profile')

@login_required
@require_POST
def redeem_points(request):
    """Redeem loyalty points for rewards"""
    try:
        reward_type = request.POST.get('reward_type')
        points_required = int(request.POST.get('points_required', 0))
        
        loyalty = get_object_or_404(LoyaltyProgram, user=request.user)
        
        if loyalty.points >= points_required:
            loyalty.points -= points_required
            loyalty.total_redeemed_points += points_required
            loyalty.save()
            
            # Create a notification for the user
            Notification.objects.create(
                user=request.user,
                title='امتیاز رد شد',
                message=f'{points_required} امتیاز برای {reward_type} استفاده شد',
                notification_type='loyalty'
            )
            
            messages.success(request, f'امتیاز شما با موفقیت رد شد!')
            return JsonResponse({'status': 'success', 'points': loyalty.points})
        else:
            return JsonResponse({
                'status': 'error', 
                'message': 'امتیاز کافی ندارید'
            })
            
    except Exception as e:
        logger.error(f"Error redeeming points: {e}")
        return JsonResponse({'status': 'error', 'message': 'خطا در رد کردن امتیاز'})

# ===== API ENDPOINTS =====

@login_required
@ajax_error_handler
def api_recommendations(request):
    """API endpoint for recommendations"""
    try:
        limit = int(request.GET.get('limit', 6))
        recommendations_data = ai_engine.generate_recommendations(request.user, limit=limit)
        
        recommendations = []
        for rec_data in recommendations_data:
            try:
                product = Product.objects.get(id=rec_data['product_id'], stock__gt=0)
                recommendations.append({
                    'id': product.id,
                    'name': product.name,
                    'price': float(product.price),
                    'image': product.image.url if product.image else None,
                    'score': rec_data['similarity_score'],
                    'reason': rec_data['reason']
                })
            except Product.DoesNotExist:
                continue
        
        return JsonResponse({
            'recommendations': recommendations,
            'total': len(recommendations)
        })
        
    except Exception as e:
        logger.error(f"Error in API recommendations: {e}")
        return JsonResponse({'error': 'خطا در بارگیری پیشنهادات'}, status=500)

@login_required
@ajax_error_handler
def api_analytics(request):
    """API endpoint for user analytics"""
    try:
        # Get user activity data
        activities = UserActivity.objects.filter(
            user=request.user,
            timestamp__gte=timezone.now() - timedelta(days=30)
        ).order_by('-timestamp')[:10]
        
        segment = CustomerSegment.objects.filter(user=request.user).first()
        loyalty = LoyaltyProgram.objects.filter(user=request.user).first()
        
        data = {
            'recent_activities': [{
                'action': activity.action,
                'page': activity.page,
                'timestamp': activity.timestamp.isoformat(),
                'product_name': activity.product.name if activity.product else None
            } for activity in activities],
            'segment': {
                'type': segment.get_segment_type_display() if segment else 'جدید',
                'total_spent': float(segment.total_spent) if segment else 0,
                'order_count': segment.order_count if segment else 0
            } if segment else None,
            'loyalty': {
                'tier': loyalty.get_tier_display() if loyalty else 'برنزی',
                'points': loyalty.points if loyalty else 0,
                'total_earned': loyalty.total_earned_points if loyalty else 0
            } if loyalty else None
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error in API analytics: {e}")
        return JsonResponse({'error': 'خطا در بارگیری تحلیلات'}, status=500) 