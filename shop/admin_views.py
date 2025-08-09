from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Q, F, DecimalField
from django.db.models.functions import TruncDate
from django.core.cache import cache
import csv
from .models import Order, OrderItem, Product, UserProfile, Notification, OrderFeedback
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test

# Helper to check advanced analytics permission
def _can_view_advanced(user):
    return user.is_staff and (user.is_superuser or user.has_perm('shop.view_advanced_analytics'))

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

@staff_member_required
@user_passes_test(_can_view_advanced)
def admin_analytics_data(request):
    """Return analytics datasets for the admin dashboard as JSON.
    Supports ?range=7d|30d|90d and optional ?granularity=day (default).
    """
    date_range = request.GET.get('range', '30d')
    granularity = request.GET.get('granularity', 'day')

    # Normalize range
    days_map = {'7d': 7, '30d': 30, '90d': 90}
    days = days_map.get(date_range, 30)

    now = timezone.now()
    start_date = (now - timedelta(days=days)).date()

    cache_key = f"admin_analytics:{days}:{granularity}"
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached)

    # Map revenue statuses to realized revenue states
    revenue_statuses = ['ready', 'shipping_preparation', 'in_transit', 'pickup_ready']

    # Time series revenue (by day)
    orders_qs = (
        Order.objects.filter(created_at__date__gte=start_date, status__in=revenue_statuses)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(total=Sum('total_amount'))
        .order_by('day')
    )
    revenue_labels = [o['day'].strftime('%Y-%m-%d') for o in orders_qs]
    revenue_values = [float(o['total'] or 0) for o in orders_qs]

    # Orders by status counts (current window)
    status_counts = (
        Order.objects.filter(created_at__date__gte=start_date)
        .values('status')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    orders_by_status = {row['status']: row['count'] for row in status_counts}

    # Top products (by qty sold)
    top_products_qs = (
        Product.objects.annotate(total_qty=Sum('orderitem__quantity'))
        .order_by('-total_qty')[:10]
        .values('id', 'name', 'total_qty')
    )
    top_products = [
        {"id": p['id'], "name": p['name'], "total_qty": int(p['total_qty'] or 0)} for p in top_products_qs
    ]

    # Revenue by category (sum of order items price*qty)
    order_items = (
        OrderItem.objects.filter(order__created_at__date__gte=start_date)
        .values('product__category__name')
        .annotate(
            revenue=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=12, decimal_places=2))
        )
        .order_by('-revenue')[:10]
    )
    revenue_by_category = [
        {"category": row['product__category__name'] or 'نامشخص', "revenue": float(row['revenue'] or 0)}
        for row in order_items
    ]

    # Low stock list (top 10)
    low_stock = list(
        Product.objects.filter(stock__lte=5).values('id', 'name', 'stock').order_by('stock')[:10]
    )

    # Active users (by orders in range)
    active_users_qs = (
        User.objects.filter(order__created_at__date__gte=start_date)
        .annotate(order_count=Count('order'))
        .order_by('-order_count')[:10]
        .values('id', 'username', 'order_count')
    )
    active_users = [
        {"id": u['id'], "username": u['username'], "order_count": u['order_count']} for u in active_users_qs
    ]

    # KPIs
    total_orders_window = Order.objects.filter(created_at__date__gte=start_date).count()
    total_revenue_window = (
        Order.objects.filter(created_at__date__gte=start_date, status__in=revenue_statuses)
        .aggregate(s=Sum('total_amount'))['s'] or 0
    )
    aov = float(total_revenue_window) / total_orders_window if total_orders_window else 0.0

    # Repeat rate (users with >1 order in window / users with >=1 order)
    users_with_orders = (
        User.objects.filter(order__created_at__date__gte=start_date)
        .annotate(c=Count('order'))
    )
    repeat_customers = users_with_orders.filter(c__gt=1).count()
    total_unique_customers = users_with_orders.count()
    repeat_rate = (repeat_customers / total_unique_customers) * 100 if total_unique_customers else 0.0

    # Conversion approximation: orders in window / active users (basic placeholder)
    active_users_count = UserProfile.objects.filter(created_at__date__lte=now.date()).count() or 1
    conversion_rate = (total_orders_window / active_users_count) * 100

    # Cohort by week: new users per week
    cohort_qs = (
        UserProfile.objects.filter(created_at__date__gte=start_date)
        .annotate(week=TruncDate('created_at'))
        .values('week')
        .annotate(new_users=Count('id'))
        .order_by('week')
    )
    cohort = [{ 'week': row['week'].strftime('%Y-%m-%d'), 'new_users': row['new_users']} for row in cohort_qs]

    payload = {
        'range': date_range,
        'granularity': granularity,
        'revenue_timeseries': {
            'labels': revenue_labels,
            'values': revenue_values,
        },
        'orders_by_status': orders_by_status,
        'top_products': top_products,
        'revenue_by_category': revenue_by_category,
        'low_stock': low_stock,
        'active_users': active_users,
    }

    payload.update({
        'kpi': {
            'aov': aov,
            'repeat_rate': repeat_rate,
            'conversion_rate': conversion_rate,
        },
        'cohort_new_users': cohort,
    })

    cache.set(cache_key, payload, 60)  # cache for 60 seconds
    return JsonResponse(payload)

@staff_member_required
@user_passes_test(_can_view_advanced)
def admin_analytics_top_products(request):
    date_range = request.GET.get('range', '30d')
    days_map = {'7d': 7, '30d': 30, '90d': 90}
    days = days_map.get(date_range, 30)
    start_date = (timezone.now() - timedelta(days=days)).date()

    qs = (
        Product.objects.annotate(total_qty=Sum('orderitem__quantity'))
        .filter(orderitem__order__created_at__date__gte=start_date)
        .order_by('-total_qty')[:50]
        .values('id', 'name', 'total_qty')
    )
    return JsonResponse(list(qs), safe=False)

@staff_member_required
@user_passes_test(_can_view_advanced)
def admin_analytics_category_breakdown(request):
    date_range = request.GET.get('range', '30d')
    days_map = {'7d': 7, '30d': 30, '90d': 90}
    days = days_map.get(date_range, 30)
    start_date = (timezone.now() - timedelta(days=days)).date()

    items = (
        OrderItem.objects.filter(order__created_at__date__gte=start_date)
        .values('product__category__name')
        .annotate(revenue=Sum(F('price') * F('quantity'), output_field=DecimalField(max_digits=12, decimal_places=2)))
        .order_by('-revenue')
    )
    data = [{ 'category': r['product__category__name'] or 'نامشخص', 'revenue': float(r['revenue'] or 0)} for r in items]
    return JsonResponse(data, safe=False)


@staff_member_required
def admin_export_orders_csv(request):
    """Export orders within a date range as CSV. Supports ?from=YYYY-MM-DD&to=YYYY-MM-DD"""
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')

    today = timezone.now().date()
    if not date_from:
        date_from = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    if not date_to:
        date_to = today.strftime('%Y-%m-%d')

    try:
        start = datetime.strptime(date_from, '%Y-%m-%d').date()
        end = datetime.strptime(date_to, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format, expected YYYY-MM-DD'}, status=400)

    qs = (
        Order.objects.filter(created_at__date__gte=start, created_at__date__lte=end)
        .select_related('user')
        .order_by('-created_at')
    )

    response = redirect('/')  # placeholder to make type checker happy
    # Build CSV response
    response = render(request, 'admin/index.html')
    response = JsonResponse({'ok': True})

    # Rebuild as HttpResponse CSV
    from django.http import HttpResponse
    resp = HttpResponse(content_type='text/csv')
    filename = f"orders_{date_from}_to_{date_to}.csv"
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(resp)
    writer.writerow(['Order ID', 'User', 'Status', 'Subtotal', 'Delivery Fee', 'Total', 'Created At'])
    for o in qs:
        writer.writerow([
            o.id,
            getattr(o.user, 'username', ''),
            o.status,
            o.subtotal,
            o.delivery_fee,
            o.total_amount,
            o.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])

    return resp