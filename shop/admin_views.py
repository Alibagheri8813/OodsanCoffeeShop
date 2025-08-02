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
    
    revenue_today = Order.objects.filter(created_at__date=today, status__in=['delivered', 'shipped']).aggregate(
        total=Sum('total_amount'))['total'] or 0
    revenue_yesterday = Order.objects.filter(created_at__date=yesterday, status__in=['delivered', 'shipped']).aggregate(
        total=Sum('total_amount'))['total'] or 0
    revenue_growth = ((revenue_today - revenue_yesterday) / revenue_yesterday * 100) if revenue_yesterday > 0 else 0
    
    new_users_today = UserProfile.objects.filter(created_at__date=today).count()
    
    # Order status counts
    pending_orders = Order.objects.filter(status='pending').count()
    processing_orders = Order.objects.filter(status='processing').count()
    shipped_orders = Order.objects.filter(status='shipped').count()
    
    # Weekly and monthly revenue
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    revenue_week = Order.objects.filter(
        created_at__date__gte=week_ago,
        status__in=['delivered', 'shipped']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    revenue_month = Order.objects.filter(
        created_at__date__gte=month_ago,
        status__in=['delivered', 'shipped']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Alerts
    urgent_orders = Order.objects.filter(status='pending').order_by('created_at')[:5]
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
    }
    
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
def mark_notification_read(request):
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.mark_as_read()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

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
    pending_count = Order.objects.filter(status='pending').count()
    processing_count = Order.objects.filter(status='processing').count()
    shipped_count = Order.objects.filter(status='shipped').count()
    delivered_count = Order.objects.filter(status='delivered').count()
    
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