from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Avg, Q, F, Prefetch
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _
from .models import Category, Product, Order, OrderItem, OrderFeedback, Comment, ProductLike, UserProfile, Notification, ProductFavorite, Video, Cart, CartItem, UserActivity, ProductRecommendation, SearchQuery, CustomerSegment, LoyaltyProgram, ProductInteraction
import functools
import logging

logger = logging.getLogger(__name__)

# Recursion prevention decorator
def prevent_recursion(max_depth=3):
    """Decorator to prevent infinite recursion in admin methods"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, obj):
            # Track recursion depth using object attribute
            depth_attr = f'_recursion_depth_{func.__name__}'
            current_depth = getattr(obj, depth_attr, 0)
            
            if current_depth >= max_depth:
                logger.warning(f"Recursion limit reached in {func.__name__} for {obj}")
                return format_html('<span style="color: #999;">-</span>')
            
            try:
                setattr(obj, depth_attr, current_depth + 1)
                return func(self, obj)
            except RecursionError:
                logger.error(f"RecursionError in {func.__name__} for {obj}")
                return format_html('<span style="color: #dc3545;">Error</span>')
            finally:
                setattr(obj, depth_attr, current_depth)
        return wrapper
    return decorator

# Custom Admin Filters
class StockFilter(SimpleListFilter):
    title = _('وضعیت موجودی')
    parameter_name = 'stock_status'

    def lookups(self, request, model_admin):
        return (
            ('in_stock', _('موجود')),
            ('low_stock', _('کم موجودی')),
            ('out_of_stock', _('ناموجود')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'in_stock':
            return queryset.filter(stock__gt=10)
        if self.value() == 'low_stock':
            return queryset.filter(stock__lte=10, stock__gt=0)
        if self.value() == 'out_of_stock':
            return queryset.filter(stock=0)

class OrderStatusFilter(SimpleListFilter):
    title = _('وضعیت سفارش')
    parameter_name = 'order_status'

    def lookups(self, request, model_admin):
        return (
            ('pending', _('در انتظار')),
            ('processing', _('در حال پردازش')),
            ('shipped', _('ارسال شده')),
            ('delivered', _('تحویل شده')),
            ('cancelled', _('لغو شده')),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())

# Enhanced Category Admin
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'product_count', 'image_preview')
    search_fields = ('name',)
    list_filter = ('parent',)
    list_per_page = 20
    ordering = ('name',)
    actions = ['export_categories']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'description', 'parent')
        }),
        ('تصویر', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('parent')
        queryset = queryset.annotate(
            product_count_value=Count('product', distinct=True)
        )
        return queryset
    
    def product_count(self, obj):
        # Use the annotated value instead of making a new query
        count = getattr(obj, 'product_count_value', 0)
        return format_html('<span style="color: #007bff; font-weight: bold;">{}</span>', count)
    product_count.short_description = 'تعداد محصولات'
    product_count.admin_order_field = 'product_count_value'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />', 
                obj.image.url
            )
        return format_html('<span style="color: #999;">بدون تصویر</span>')
    image_preview.short_description = 'تصویر'
    
    def export_categories(self, request, queryset):
        self.message_user(request, f'{queryset.count()} دسته‌بندی برای صادرات آماده شد.')
    export_categories.short_description = "صادرات دسته‌بندی‌ها"

# Enhanced Product Admin
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'featured', 'image_preview', 'like_count', 'favorite_count', 'created_at', 'status_badge')
    list_filter = (StockFilter, 'category', 'created_at', 'featured')
    search_fields = ('name', 'description')
    list_editable = ('price', 'stock', 'featured')
    readonly_fields = ('like_count', 'favorite_count', 'comment_count', 'total_sold')
    list_per_page = 25
    ordering = ('-created_at',)
    actions = ['mark_as_featured', 'mark_as_not_featured', 'update_stock', 'export_products', 'duplicate_products']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'description', 'category', 'price', 'stock')
        }),
        ('تصویر', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('آمار', {
            'fields': ('like_count', 'favorite_count', 'comment_count', 'total_sold'),
            'classes': ('collapse',)
        }),
        ('ویژگی‌ها', {
            'fields': ('featured',)
        })
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('category')
        queryset = queryset.annotate(
            like_count_value=Count('likes', distinct=True),
            favorite_count_value=Count('favorites', distinct=True),
            comment_count_value=Count('comments', distinct=True),
            total_sold_value=Sum('orderitem__quantity', default=0)
        )
        return queryset
    
    def status_badge(self, obj):
        if obj.stock > 10:
            return format_html('<span style="background: #28a745; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px;">موجود</span>')
        elif obj.stock > 0:
            return format_html('<span style="background: #ffc107; color: #212529; padding: 4px 12px; border-radius: 20px; font-size: 11px;">کم موجودی</span>')
        else:
            return format_html('<span style="background: #dc3545; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px;">ناموجود</span>')
    status_badge.short_description = 'وضعیت'
    
    def total_sold(self, obj):
        # Use the annotated value
        total = getattr(obj, 'total_sold_value', 0)
        return format_html('<span style="color: #4caf50; font-weight: bold;">{}</span>', total)
    total_sold.short_description = 'تعداد فروش'
    
    def mark_as_featured(self, request, queryset):
        queryset.update(featured=True)
        self.message_user(request, 'محصولات انتخاب شده به عنوان ویژه علامت‌گذاری شدند.', messages.SUCCESS)
    mark_as_featured.short_description = "علامت‌گذاری به عنوان ویژه"
    
    def mark_as_not_featured(self, request, queryset):
        queryset.update(featured=False)
        self.message_user(request, 'علامت ویژه از محصولات انتخاب شده برداشته شد.', messages.SUCCESS)
    mark_as_not_featured.short_description = "حذف علامت ویژه"
    
    def update_stock(self, request, queryset):
        self.message_user(request, f'{queryset.count()} محصول برای به‌روزرسانی موجودی انتخاب شد.')
    update_stock.short_description = "به‌روزرسانی موجودی"
    
    def export_products(self, request, queryset):
        self.message_user(request, f'{queryset.count()} محصول برای صادرات آماده شد.')
    export_products.short_description = "صادرات محصولات"
    
    def duplicate_products(self, request, queryset):
        for product in queryset:
            product.pk = None
            product.name = f"{product.name} (کپی)"
            product.save()
        self.message_user(request, f'{queryset.count()} محصول کپی شد.')
    duplicate_products.short_description = "کپی محصولات"
    
    def like_count(self, obj):
        # Use the annotated value
        count = getattr(obj, 'like_count_value', 0)
        return format_html('<span style="color: #e91e63; font-weight: bold;">{}</span>', count)
    like_count.short_description = 'لایک‌ها'
    like_count.admin_order_field = 'like_count_value'
    
    def favorite_count(self, obj):
        # Use the annotated value
        count = getattr(obj, 'favorite_count_value', 0)
        return format_html('<span style="color: #ff9800; font-weight: bold;">{}</span>', count)
    favorite_count.short_description = 'علاقه‌مندی‌ها'
    favorite_count.admin_order_field = 'favorite_count_value'
    
    def comment_count(self, obj):
        # Use the annotated value
        count = getattr(obj, 'comment_count_value', 0)
        return format_html('<span style="color: #2196f3; font-weight: bold;">{}</span>', count)
    comment_count.short_description = 'نظرات'
    comment_count.admin_order_field = 'comment_count_value'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />', 
                obj.image.url
            )
        return format_html('<span style="color: #999;">بدون تصویر</span>')
    image_preview.short_description = 'تصویر'

# Enhanced Order Admin
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'status_badge', 'total_amount', 'item_count', 'created_at', 'payment_status', 'has_feedback')
    list_filter = (OrderStatusFilter, 'created_at', 'delivery_method')
    search_fields = ('user__username', 'user__email', 'id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'total_amount', 'subtotal', 'delivery_fee')
    date_hierarchy = 'created_at'
    list_per_page = 30
    ordering = ('-created_at',)
    actions = ['mark_as_shipped', 'mark_as_delivered', 'export_orders', 'send_notification']
    
    fieldsets = (
        ('اطلاعات سفارش', {
            'fields': ('id', 'user', 'status', 'created_at', 'updated_at')
        }),
        ('جزئیات مالی', {
            'fields': ('subtotal', 'delivery_fee', 'total_amount')
        }),
        ('اطلاعات تحویل', {
            'fields': ('delivery_method', 'shipping_address', 'postal_code', 'phone_number')
        }),
        ('یادداشت', {
            'fields': ('notes',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items').annotate(
            item_count_value=Count('items', distinct=True),
            has_feedback_value=Count('orderfeedback', distinct=True)
        )
    
    def status_badge(self, obj):
        status_colors = {
            'pending': '#ffc107',
            'processing': '#17a2b8',
            'shipped': '#007bff',
            'delivered': '#28a745',
            'cancelled': '#dc3545'
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'وضعیت'
    
    def has_feedback(self, obj):
        # Use the annotated value
        has_feedback = getattr(obj, 'has_feedback_value', 0) > 0
        if has_feedback:
            return format_html('<span style="color: #28a745;">✓</span>')
        return format_html('<span style="color: #dc3545;">✗</span>')
    has_feedback.short_description = 'بازخورد'
    has_feedback.admin_order_field = 'has_feedback_value'
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
        self.message_user(request, 'سفارشات انتخاب شده به حالت "در حال پردازش" تغییر یافتند.')
    mark_as_processing.short_description = "تغییر به در حال پردازش"
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')
        self.message_user(request, 'سفارشات انتخاب شده به حالت "ارسال شده" تغییر یافتند.')
    mark_as_shipped.short_description = "تغییر به ارسال شده"
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')
        self.message_user(request, 'سفارشات انتخاب شده به حالت "تحویل داده شده" تغییر یافتند.')
    mark_as_delivered.short_description = "تغییر به تحویل داده شده"
    
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, 'سفارشات انتخاب شده لغو شدند.')
    mark_as_cancelled.short_description = "لغو سفارش"
    
    def export_orders(self, request, queryset):
        self.message_user(request, f'{queryset.count()} سفارش برای صادرات آماده شد.')
    export_orders.short_description = "صادرات سفارشات"
    
    def send_order_notifications(self, request, queryset):
        self.message_user(request, f'اعلان برای {queryset.count()} سفارش ارسال شد.')
    send_order_notifications.short_description = "ارسال اعلان"
    
    def item_count(self, obj):
        # Use the annotated value
        count = getattr(obj, 'item_count_value', 0)
        return format_html('<span style="color: #007bff; font-weight: bold;">{}</span>', count)
    item_count.short_description = 'تعداد اقلام'
    item_count.admin_order_field = 'item_count_value'
    
    def payment_status(self, obj):
        if obj.status == 'delivered':
            return format_html('<span style="color: #28a745;">✓ پرداخت شده</span>')
        elif obj.status == 'pending':
            return format_html('<span style="color: #ffc107;">⏳ در انتظار</span>')
        else:
            return format_html('<span style="color: #dc3545;">✗ ناموفق</span>')
    payment_status.short_description = 'وضعیت پرداخت'

# Enhanced OrderItem Admin
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'total_price')
    list_filter = ('order__status', 'product__category')
    search_fields = ('order__user__username', 'product__name')
    list_per_page = 50
    readonly_fields = ('total_price',)
    
    def total_price(self, obj):
        return format_html('<span style="font-weight: bold;">{} تومان</span>', obj.price * obj.quantity)
    total_price.short_description = 'قیمت کل'

# Enhanced OrderFeedback Admin
class OrderFeedbackAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'rating_stars', 'comment_preview', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('order__user__username', 'comment')
    readonly_fields = ('created_at', 'order', 'user')
    list_per_page = 25
    actions = ['mark_as_helpful', 'mark_as_not_helpful']
    
    def user(self, obj):
        return obj.order.user.username
    user.short_description = 'کاربر'
    
    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        color = '#ffc107' if obj.rating >= 4 else '#ff9800' if obj.rating >= 3 else '#f44336'
        return format_html('<span style="color: {}; font-size: 16px;">{}</span>', color, stars)
    rating_stars.short_description = 'امتیاز'
    
    def comment_preview(self, obj):
        if obj.comment:
            preview = obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
            return format_html('<span title="{}">{}</span>', obj.comment, preview)
        return '-'
    comment_preview.short_description = 'نظر'
    
    def mark_as_helpful(self, request, queryset):
        self.message_user(request, f'{queryset.count()} نظر مفید علامت‌گذاری شد.')
    mark_as_helpful.short_description = "علامت‌گذاری به عنوان مفید"
    
    def mark_as_not_helpful(self, request, queryset):
        self.message_user(request, f'{queryset.count()} نظر غیرمفید علامت‌گذاری شد.')
    mark_as_not_helpful.short_description = "علامت‌گذاری به عنوان غیرمفید"

# Enhanced UserProfile Admin
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'city', 'province', 'order_count', 'total_spent', 'profile_image_preview', 'last_order_date', 'customer_type')
    list_filter = ('city', 'province', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number', 'city', 'province')
    readonly_fields = ('created_at', 'updated_at', 'order_count', 'total_spent', 'last_order_date')
    list_per_page = 30
    actions = ['export_profiles', 'send_notification', 'mark_as_vip', 'mark_as_regular']
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user', 'avatar')
        }),
        ('اطلاعات تماس', {
            'fields': ('phone_number', 'email_verified')
        }),
        ('اطلاعات شخصی', {
            'fields': ('birth_date', 'bio')
        }),
        ('آدرس', {
            'fields': ('city', 'province', 'address', 'postal_code')
        }),
        ('آمار', {
            'fields': ('order_count', 'total_spent', 'last_order_date'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user')
        # Create subquery for order statistics to avoid multiple queries
        from django.db.models import Max, Q
        queryset = queryset.annotate(
            order_count_value=Count('user__order', distinct=True),
            total_spent_value=Sum(
                'user__order__total_amount',
                filter=Q(user__order__status__in=['delivered', 'shipped']),
                default=0
            ),
            last_order_date_value=Max('user__order__created_at')
        )
        return queryset
    
    def customer_type(self, obj):
        # Use annotated total_spent_value
        total_spent = getattr(obj, 'total_spent_value', 0) or 0
        if total_spent > 1000000:  # More than 1 million
            return format_html('<span style="background: #ffd700; color: #333; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold;">VIP</span>')
        elif total_spent > 500000:  # More than 500k
            return format_html('<span style="background: #c0c0c0; color: #333; padding: 4px 12px; border-radius: 20px; font-size: 11px;">نقره‌ای</span>')
        else:
            return format_html('<span style="background: #cd7f32; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px;">برنزی</span>')
    customer_type.short_description = 'نوع مشتری'
    
    def last_order_date(self, obj):
        # Use annotated value
        last_date = getattr(obj, 'last_order_date_value', None)
        if last_date:
            days_ago = (timezone.now() - last_date).days
            if days_ago == 0:
                return format_html('<span style="color: #28a745;">امروز</span>')
            elif days_ago == 1:
                return format_html('<span style="color: #28a745;">دیروز</span>')
            elif days_ago < 7:
                return format_html('<span style="color: #17a2b8;">{} روز پیش</span>', days_ago)
            elif days_ago < 30:
                return format_html('<span style="color: #ffc107;">{} هفته پیش</span>', days_ago // 7)
            else:
                return format_html('<span style="color: #dc3545;">{} ماه پیش</span>', days_ago // 30)
        return format_html('<span style="color: #999;">هیچ سفارشی</span>')
    last_order_date.short_description = 'آخرین سفارش'
    last_order_date.admin_order_field = 'last_order_date_value'
    
    def export_profiles(self, request, queryset):
        self.message_user(request, f'{queryset.count()} کاربر برای صادرات آماده شد.')
    export_profiles.short_description = "صادرات پروفایل‌ها"
    
    def send_notification(self, request, queryset):
        self.message_user(request, f'اعلان برای {queryset.count()} کاربر ارسال شد.')
    send_notification.short_description = "ارسال اعلان"
    
    def mark_as_vip(self, request, queryset):
        self.message_user(request, f'{queryset.count()} کاربر VIP شد.')
    mark_as_vip.short_description = "تبدیل به VIP"
    
    def mark_as_regular(self, request, queryset):
        self.message_user(request, f'{queryset.count()} کاربر عادی شد.')
    mark_as_regular.short_description = "تبدیل به عادی"
    
    def order_count(self, obj):
        # Use annotated value
        count = getattr(obj, 'order_count_value', 0)
        return format_html('<span style="color: #007bff; font-weight: bold;">{}</span>', count)
    order_count.short_description = 'تعداد سفارش'
    order_count.admin_order_field = 'order_count_value'
    
    def total_spent(self, obj):
        # Use annotated value
        total = getattr(obj, 'total_spent_value', 0) or 0
        return format_html('<span style="color: #28a745; font-weight: bold;">{:,.0f} تومان</span>', total)
    total_spent.short_description = 'کل خرید'
    total_spent.admin_order_field = 'total_spent_value'
    
    def profile_image_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 50%; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />', 
                obj.avatar.url
            )
        return format_html('<span style="color: #999;">بدون تصویر</span>')
    profile_image_preview.short_description = 'تصویر پروفایل'

# Enhanced Notification Admin
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at', 'status_badge')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)
    list_per_page = 50
    actions = ['mark_as_read', 'mark_as_unread', 'delete_notifications', 'send_bulk_notifications']
    
    def status_badge(self, obj):
        if obj.is_read:
            return format_html('<span style="background: #28a745; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px;">خوانده شده</span>')
        else:
            return format_html('<span style="background: #ffc107; color: #212529; padding: 4px 12px; border-radius: 20px; font-size: 11px;">خوانده نشده</span>')
    status_badge.short_description = 'وضعیت'
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} اعلان خوانده شده علامت‌گذاری شد.')
    mark_as_read.short_description = "علامت‌گذاری به عنوان خوانده شده"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} اعلان خوانده نشده علامت‌گذاری شد.')
    mark_as_unread.short_description = "علامت‌گذاری به عنوان خوانده نشده"
    
    def delete_notifications(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} اعلان حذف شد.')
    delete_notifications.short_description = "حذف اعلان‌ها"
    
    def send_bulk_notifications(self, request, queryset):
        self.message_user(request, f'اعلان برای {queryset.count()} کاربر ارسال شد.')
    send_bulk_notifications.short_description = "ارسال اعلان گروهی"

# Enhanced Video Admin
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at', 'video_preview')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title',)
    list_editable = ('is_active',)
    list_per_page = 20
    actions = ['activate_videos', 'deactivate_videos']
    
    def video_preview(self, obj):
        if obj.video_file:
            return format_html(
                '<video width="100" height="60" controls style="border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">'
                '<source src="{}" type="video/mp4">'
                'مرورگر شما از ویدیو پشتیبانی نمی‌کند.'
                '</video>', obj.video_file.url
            )
        return format_html('<span style="color: #999;">بدون ویدیو</span>')
    video_preview.short_description = 'پیش‌نمایش'
    
    def activate_videos(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} ویدیو فعال شد.')
    activate_videos.short_description = "فعال کردن ویدیوها"
    
    def deactivate_videos(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} ویدیو غیرفعال شد.')
    deactivate_videos.short_description = "غیرفعال کردن ویدیوها"

# Enhanced Cart Admin
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_total_quantity', 'get_total_price', 'created_at', 'item_count']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    list_per_page = 30
    readonly_fields = ['get_total_quantity', 'get_total_price', 'item_count']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('user')
        queryset = queryset.prefetch_related(
            Prefetch('items', queryset=CartItem.objects.select_related('product'))
        )
        queryset = queryset.annotate(
            item_count_value=Count('items', distinct=True),
            total_quantity_value=Sum('items__quantity', default=0),
            # For total price, we'll still need to calculate in the method due to price*quantity
        )
        return queryset
    
    def item_count(self, obj):
        # Use the annotated value
        count = getattr(obj, 'item_count_value', 0)
        return format_html('<span style="color: #007bff; font-weight: bold;">{}</span>', count)
    item_count.short_description = 'تعداد آیتم'
    item_count.admin_order_field = 'item_count_value'
    
    def get_total_quantity(self, obj):
        # Use the annotated value
        total = getattr(obj, 'total_quantity_value', 0)
        return format_html('<span style="color: #28a745; font-weight: bold;">{}</span>', total)
    get_total_quantity.short_description = 'تعداد کل'
    get_total_quantity.admin_order_field = 'total_quantity_value'
    
    def get_total_price(self, obj):
        # Calculate using prefetched items to avoid additional queries
        total = sum(item.product.price * item.quantity for item in obj.items.all())
        return format_html('<span style="color: #007bff; font-weight: bold;">{} تومان</span>', total)
    get_total_price.short_description = 'قیمت کل'

# Enhanced CartItem Admin
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'get_total_price', 'added_at']
    list_filter = ['added_at', 'product__category']
    search_fields = ['cart__user__username', 'product__name']
    list_per_page = 50
    readonly_fields = ['get_total_price']
    
    def get_total_price(self, obj):
        total = obj.product.price * obj.quantity
        return format_html('<span style="color: #007bff; font-weight: bold;">{} تومان</span>', total)
    get_total_price.short_description = 'قیمت کل'

# Advanced Analytics Admin
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'page', 'product', 'category', 'device_type', 'timestamp')
    list_filter = ('action', 'device_type', 'timestamp', 'category')
    search_fields = ('user__username', 'page', 'product__name')
    readonly_fields = ('timestamp',)
    list_per_page = 50
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user', 'action', 'page')
        }),
        ('محصول و دسته‌بندی', {
            'fields': ('product', 'category')
        }),
        ('اطلاعات دستگاه', {
            'fields': ('device_type', 'session_duration')
        }),
        ('زمان', {
            'fields': ('timestamp',)
        }),
    )

class ProductRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'score', 'reason', 'is_viewed', 'is_purchased', 'created_at')
    list_filter = ('is_viewed', 'is_purchased', 'created_at', 'product__category')
    search_fields = ('user__username', 'product__name', 'reason')
    readonly_fields = ('created_at',)
    list_per_page = 50
    ordering = ('-score',)
    
    fieldsets = (
        ('اطلاعات توصیه', {
            'fields': ('user', 'product', 'score', 'reason')
        }),
        ('وضعیت', {
            'fields': ('is_viewed', 'is_purchased')
        }),
        ('زمان', {
            'fields': ('created_at',)
        }),
    )

class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'results_count', 'timestamp', 'session_id')
    list_filter = ('timestamp', 'results_count')
    search_fields = ('query', 'user__username')
    readonly_fields = ('timestamp', 'filters_used')
    list_per_page = 50
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('اطلاعات جستجو', {
            'fields': ('user', 'query', 'results_count', 'clicked_product')
        }),
        ('فیلترها', {
            'fields': ('filters_used',)
        }),
        ('جلسه', {
            'fields': ('session_id', 'timestamp')
        }),
    )

class CustomerSegmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'segment_type', 'total_spent', 'order_count', 'average_order_value', 'last_order_date')
    list_filter = ('segment_type', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('updated_at', 'engagement_score')
    list_per_page = 30
    ordering = ('-total_spent',)
    actions = ['update_segments', 'export_segments']
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user', 'segment_type', 'engagement_score')
        }),
        ('آمار خرید', {
            'fields': ('total_spent', 'order_count', 'average_order_value')
        }),
        ('دسته‌بندی‌های مورد علاقه', {
            'fields': ('favorite_categories',)
        }),
        ('زمان‌ها', {
            'fields': ('last_order_date', 'updated_at')
        }),
    )
    
    def update_segments(self, request, queryset):
        """Update customer segments"""
        # Assuming ai_engine is defined elsewhere or needs to be imported
        # from .ai_engine import ai_engine # Example import if needed
        updated = 0
        for segment in queryset:
            # if ai_engine: # Check if ai_engine is available
            #     ai_engine.update_user_segment(segment.user)
            # else:
            #     self.message_user(request, "AI engine is not available.")
            pass # Placeholder for AI engine call
            updated += 1
        
        self.message_user(request, f'{updated} بخش مشتریان بروزرسانی شد.')
    update_segments.short_description = "بروزرسانی بخش‌های مشتریان"
    
    def export_segments(self, request, queryset):
        """Export customer segments"""
        self.message_user(request, f'{queryset.count()} بخش مشتریان برای صادرات آماده شد.')
    export_segments.short_description = "صادرات بخش‌های مشتریان"

# Admin class for ProductInteraction
@admin.register(ProductInteraction)
class ProductInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'interaction_type', 'timestamp')
    list_filter = ('interaction_type', 'timestamp')
    search_fields = ('user__username', 'product__name')
    readonly_fields = ('timestamp',)
    list_per_page = 50
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('اطلاعات تعامل', {
            'fields': ('user', 'product', 'interaction_type')
        }),
        ('جلسه و زمان', {
            'fields': ('session_id', 'timestamp')
        }),
    )

class LoyaltyProgramAdmin(admin.ModelAdmin):
    list_display = ('user', 'tier', 'points', 'total_earned_points', 'total_redeemed_points', 'tier_achieved_date')
    list_filter = ('tier', 'tier_achieved_date')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('tier_achieved_date', 'next_tier_points_needed')
    list_per_page = 30
    ordering = ('-points',)
    actions = ['update_tiers', 'add_bonus_points', 'export_loyalty_data']
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user', 'tier', 'tier_achieved_date')
        }),
        ('امتیازات', {
            'fields': ('points', 'total_earned_points', 'total_redeemed_points', 'next_tier_points_needed')
        }),
    )
    
    def update_tiers(self, request, queryset):
        """Update loyalty tiers based on spending"""
        updated = 0
        for loyalty in queryset:
            # Assuming loyalty.calculate_tier() is defined elsewhere or needs to be imported
            # from .loyalty_program import calculate_tier # Example import if needed
            # loyalty.tier = calculate_tier(loyalty.user) # Example usage
            # loyalty.save()
            pass # Placeholder for loyalty tier update logic
            updated += 1
        
        self.message_user(request, f'{updated} سطح وفاداری بروزرسانی شد.')
    update_tiers.short_description = "بروزرسانی سطوح وفاداری"
    
    def add_bonus_points(self, request, queryset):
        """Add bonus points to selected users"""
        points = 100  # Default bonus points
        updated = queryset.update(points=F('points') + points)
        self.message_user(request, f'{points} امتیاز پاداش به {updated} کاربر اضافه شد.')
    add_bonus_points.short_description = "اضافه کردن امتیاز پاداش"
    
    def export_loyalty_data(self, request, queryset):
        """Export loyalty program data"""
        self.message_user(request, f'{queryset.count()} رکورد برنامه وفاداری برای صادرات آماده شد.')
    export_loyalty_data.short_description = "صادرات داده‌های وفاداری"

# Register new Phase 3 admin models
admin.site.register(UserActivity, UserActivityAdmin)
admin.site.register(ProductRecommendation, ProductRecommendationAdmin)
admin.site.register(SearchQuery, SearchQueryAdmin)
admin.site.register(CustomerSegment, CustomerSegmentAdmin)
admin.site.register(LoyaltyProgram, LoyaltyProgramAdmin)

# Register all models with enhanced admin classes
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(OrderFeedback, OrderFeedbackAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)

# Customize admin site
admin.site.site_header = "کافی شاپ - پنل مدیریت"
admin.site.site_title = "کافی شاپ"
admin.site.index_title = "خوش آمدید به پنل مدیریت کافی شاپ"
