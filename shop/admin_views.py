from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Q
from .models import Order, OrderItem, Product, UserProfile, Notification, OrderFeedback
from django.contrib.auth.models import User

@staff_member_required
def admin_dashboard(request):
    # Get current date and time
    now = timezone.now()
    today = now.date()
    yesterday = today - timedelta(days=1)
    
    # Basic statistics
    total_orders = Order.objects.count()
    total_products = Product.objects.count()
    active_users = UserProfile.objects.count()
    
    # Today's statistics
    orders_today = Order.objects.filter(created_at__date=today).count()
    orders_yesterday = Order.objects.filter(created_at__date=yesterday).count()
    orders_growth = ((orders_today - orders_yesterday) / orders_yesterday * 100) if orders_yesterday > 0 else 0
    
    # Map legacy concepts (delivered/shipped) to existing statuses
    revenue_statuses = ['ready', 'shipping_preparation', 'in_transit', 'pickup_ready']
    
    revenue_today = Order.objects.filter(created_at__date=today, status__in=revenue_statuses).aggregate(
        total=Sum('total_amount'))["total"] or 0
    revenue_yesterday = Order.objects.filter(created_at__date=yesterday, status__in=revenue_statuses).aggregate(
        total=Sum('total_amount'))["total"] or 0
    revenue_growth = ((revenue_today - revenue_yesterday) / revenue_yesterday * 100) if revenue_yesterday > 0 else 0
    
    new_users_today = UserProfile.objects.filter(created_at__date=today).count()
    
    # Order status counts (mapped to current statuses)
    pending_orders = Order.objects.filter(status='pending_payment').count()
    processing_orders = Order.objects.filter(status='preparing').count()
    shipped_orders = Order.objects.filter(status__in=['shipping_preparation', 'in_transit']).count()
    making_orders = Order.objects.filter(status='preparing').count()
    made_orders = Order.objects.filter(status='ready').count()
    
    # Weekly and monthly revenue
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    revenue_week = Order.objects.filter(
        created_at__date__gte=week_ago,
        status__in=revenue_statuses
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    revenue_month = Order.objects.filter(
        created_at__date__gte=month_ago,
        status__in=revenue_statuses
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Alerts
    urgent_orders = Order.objects.filter(status='pending_payment').order_by('created_at')[:5]
    low_stock_products = Product.objects.filter(stock__lte=5)[:5]
    low_stock_products_list = Product.objects.filter(stock__lte=5)
    recent_feedback = OrderFeedback.objects.select_related('order__user').order_by('-created_at')[:5]
    
    # Recent orders
    recent_orders = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')[:10]
    
    # Top products (by order count)
    top_products = Product.objects.annotate(
        total_sold=Count('orderitem')
    ).order_by('-total_sold')[:5]
    
    # Unread notifications count
    unread_notifications = Notification.objects.filter(is_read=False).count()
    
    # Popular products by number of times viewed
    top_viewed_products = Product.objects.annotate(
        view_count=Count('interactions', filter=Q(interactions__interaction_type='view'))
    ).order_by('-view_count')[:5]

    # Most active users (by number of orders)
    most_active_users = User.objects.annotate(
        order_count=Count('order')
    ).order_by('-order_count')[:5]

    # Include data in context
    context = {
        'total_orders': total_orders,
        'revenue_today': revenue_today,
        'active_users': active_users,
        'total_products': total_products,
        'orders_growth': orders_growth,
        'revenue_growth': revenue_growth,
        'new_users_today': new_users_today,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'shipped_orders': shipped_orders,
        'revenue_week': revenue_week,
        'revenue_month': revenue_month,
        'urgent_orders': urgent_orders,
        'low_stock_products': low_stock_products,
        'low_stock_products_list': low_stock_products_list,
        'recent_feedback': recent_feedback,
        'recent_orders': recent_orders,
        'top_products': top_products,
        'unread_notifications': unread_notifications,
        'making_orders': making_orders,
        'made_orders': made_orders,
    }
    
    context.update({
        'top_viewed_products': top_viewed_products,
        'most_active_users': most_active_users,
    })
    
    return render(request, 'admin/dashboard.html', context)

@staff_member_required
def admin_notifications(request):
    notifications = Notification.objects.select_related('user').order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    
    return render(request, 'admin/notifications.html', context)

@staff_member_required
def mark_notification_read(request, notification_id=None):
    """
    Mark a notification as read from the admin panel. The notification id can be
    supplied either as part of the URL (`/read/<id>/`) or via POST data with the
    key `notification_id`. This flexibility avoids view-signature mismatches and
    eliminates the recursion/redirect errors reported on the admin pages.
    """

    # Fallback to POST body if the id was not provided via the URL
    if request.method == 'POST' and not notification_id:
        notification_id = request.POST.get('notification_id')

    try:
        notification = Notification.objects.get(id=notification_id)
        notification.mark_as_read()

        # Return JSON for AJAX requests; otherwise redirect back to the list
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})

        return redirect('admin_notifications')

    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'}, status=404)

@staff_member_required
def mark_all_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@staff_member_required
def delete_notification(request):
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.delete()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

# New custom admin views for order management
@staff_member_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order.objects.select_related('user').prefetch_related('items__product'), id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            old_status = order.status
            order.status = new_status
            order.save()
            
            # Create notification for user
            status_names = dict(Order.STATUS_CHOICES)
            Notification.create_notification(
                user=order.user,
                notification_type='order_status',
                title='تغییر وضعیت سفارش',
                message=f'وضعیت سفارش شما #{order.id} به {status_names[new_status]} تغییر یافت.',
                related_object=order
            )
            
            messages.success(request, f'وضعیت سفارش به {status_names[new_status]} تغییر یافت.')
            return redirect('admin_order_detail', order_id=order_id)
    
    context = {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
    }
    
    return render(request, 'admin/order_detail.html', context)

@staff_member_required
def admin_order_list(request):
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    orders = Order.objects.select_related('user').prefetch_related('items')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if search_query:
        orders = orders.filter(
            Q(id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    orders = orders.order_by('-created_at')
    
    # Statistics
    total_orders = Order.objects.count()
    pending_count = Order.objects.filter(status='pending_payment').count()
    processing_count = Order.objects.filter(status='preparing').count()
    shipped_count = Order.objects.filter(status__in=['shipping_preparation', 'in_transit']).count()
    delivered_count = Order.objects.filter(status='pickup_ready').count()
    making_orders = Order.objects.filter(status='preparing').count()
    made_orders = Order.objects.filter(status='ready').count()
    
    context = {
        'orders': orders,
        'status_choices': Order.STATUS_CHOICES,
        'current_status': status_filter,
        'search_query': search_query,
        'total_orders': total_orders,
        'pending_count': pending_count,
        'processing_count': processing_count,
        'shipped_count': shipped_count,
        'delivered_count': delivered_count,
        'making_count': making_orders,
        'made_count': made_orders,
    }
    
    return render(request, 'admin/order_list.html', context)

@staff_member_required
def admin_bulk_order_status(request):
    if request.method == 'POST':
        order_ids = request.POST.getlist('order_ids')
        new_status = request.POST.get('status')
        
        if order_ids and new_status in dict(Order.STATUS_CHOICES):
            orders = Order.objects.filter(id__in=order_ids)
            updated_count = orders.update(status=new_status)
            
            # Create notifications for users
            status_names = dict(Order.STATUS_CHOICES)
            for order in orders:
                Notification.create_notification(
                    user=order.user,
                    notification_type='order_status',
                    title='تغییر وضعیت سفارش',
                    message=f'وضعیت سفارش شما #{order.id} به {status_names[new_status]} تغییر یافت.',
                    related_object=order
                )
            
            messages.success(request, f'{updated_count} سفارش به وضعیت {status_names[new_status]} تغییر یافت.')
        
    return redirect('admin_order_list')


# ---------------------------------------------------------------------------
# User Tier Management
# ---------------------------------------------------------------------------
@staff_member_required
def admin_update_user_tier(request, user_id):
    """Promote or demote a user's loyalty tier.

    Accepts only POST requests containing the new `tier` in the request body.
    Returns JSON with the human-readable tier name on success so the front-end
    can update the UI without a full refresh."""
    from .models import LoyaltyProgram  # local import to avoid circular deps

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

    user = get_object_or_404(User, id=user_id)
    new_tier = request.POST.get('tier')

    if new_tier not in dict(LoyaltyProgram.TIER_CHOICES):
        return JsonResponse({'success': False, 'error': 'Tier نامعتبر است.'}, status=400)

    loyalty, _ = LoyaltyProgram.objects.get_or_create(user=user)
    loyalty.tier = new_tier
    loyalty.save()

    return JsonResponse({'success': True, 'tier': loyalty.get_tier_display()})