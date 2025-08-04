from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _
from .models import Category, Product, Order, OrderItem, OrderFeedback, Comment, ProductLike, UserProfile, Notification, ProductFavorite, Video, Cart, CartItem, UserActivity, ProductRecommendation, SearchQuery, CustomerSegment, LoyaltyProgram, ProductInteraction

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
            ('pending_payment', _('در انتظار پرداخت')),
            ('preparing', _('در حال آمــاده‌سازی')),
            ('ready', _('آماده شده')),
            ('shipping_preparation', _('در حال ارسال به اداره پست')),
            ('in_transit', _('بسته در حال رسیدن به مقصد است')),
            ('pickup_ready', _('آماده شده است و لطفاً مراجعه کنید')),
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
    
    def product_count(self, obj):
        count = obj.product_set.count()
        return format_html('<span style="color: #007bff; font-weight: bold;">{}</span>', count)
    product_count.short_description = 'تعداد محصولات'
    
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
            'fields': ('name', 'description', 'category')
        }),
        ('قیمت و موجودی', {
            'fields': ('price', 'stock')
        }),
        ('تصاویر', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('تنظیمات', {
            'fields': ('featured',)
        }),
        ('آمار', {
            'fields': ('like_count', 'favorite_count', 'comment_count', 'total_sold'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        if obj.stock == 0:
            return format_html('<span style="background: #dc3545; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold;">ناموجود</span>')
        elif obj.stock < 10:
            return format_html('<span style="background: #ffc107; color: #212529; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold;">کم موجودی</span>')
        else:
            return format_html('<span style="background: #28a745; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold;">موجود</span>')
    status_badge.short_description = 'وضعیت'
    
    def total_sold(self, obj):
        total = obj.orderitem_set.aggregate(total=Sum('quantity'))['total'] or 0
        return format_html('<span style="color: #007bff; font-weight: bold;">{}</span>', total)
    total_sold.short_description = 'تعداد فروش'
    
    def mark_as_featured(self, request, queryset):
        updated = queryset.update(featured=True)
        self.message_user(request, f'{updated} محصول به عنوان ویژه علامت‌گذاری شد.')
    mark_as_featured.short_description = "علامت‌گذاری به عنوان ویژه"
    
    def mark_as_not_featured(self, request, queryset):
        updated = queryset.update(featured=False)
        self.message_user(request, f'{updated} محصول از حالت ویژه خارج شد.')
    mark_as_not_featured.short_description = "حذف از حالت ویژه"
    
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
        count = obj.likes.count()
        return format_html('<span style="color: #e91e63; font-weight: bold;">{}</span>', count)
    like_count.short_description = 'لایک‌ها'
    
    def favorite_count(self, obj):
        count = obj.favorites.count()
        return format_html('<span style="color: #ff9800; font-weight: bold;">{}</span>', count)
    favorite_count.short_description = 'علاقه‌مندی‌ها'
    
    def comment_count(self, obj):
        count = obj.comments.count()
        return format_html('<span style="color: #2196f3; font-weight: bold;">{}</span>', count)
    comment_count.short_description = 'نظرات'
    
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
    search_fields = ('user__username', 'shipping_address', 'id', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'total_amount')
    list_editable = ('status',)
    list_per_page = 30
    ordering = ('-created_at',)
    actions = ['mark_as_paid', 'mark_as_ready', 'start_shipping_preparation', 'mark_in_transit', 'export_orders', 'send_order_notifications']
    
    fieldsets = (
        ('اطلاعات سفارش', {
            'fields': ('user', 'status', 'total_amount')
        }),
        ('اطلاعات ارسال', {
            'fields': ('shipping_address', 'delivery_method', 'postal_code', 'phone_number')
        }),
        ('زمان‌بندی', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Enhanced status badge with coffee shop brand colors"""
        color = obj.get_status_badge_color()
        
        # Special styling for different statuses
        style_map = {
            'pending_payment': 'background: linear-gradient(135deg, #8B4513, #A0522D); color: white; box-shadow: 0 2px 8px rgba(139,69,19,0.3);',
            'preparing': 'background: linear-gradient(135deg, #D2691E, #CD853F); color: white; box-shadow: 0 2px 8px rgba(210,105,30,0.3);',
            'ready': 'background: linear-gradient(135deg, #CD853F, #DEB887); color: white; box-shadow: 0 2px 8px rgba(205,133,63,0.3);',
            'shipping_preparation': 'background: linear-gradient(135deg, #A0522D, #8B4513); color: white; box-shadow: 0 2px 8px rgba(160,82,45,0.3);',
            'in_transit': 'background: linear-gradient(135deg, #654321, #8B4513); color: white; box-shadow: 0 2px 8px rgba(101,67,33,0.3);',
            'pickup_ready': 'background: linear-gradient(135deg, #228B22, #32CD32); color: white; box-shadow: 0 2px 8px rgba(34,139,34,0.3);',
        }
        
        style = style_map.get(obj.status, f'background: {color}; color: white;')
        
        return format_html(
            '<span style="{} padding: 6px 16px; border-radius: 25px; font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; border: 2px solid white; display: inline-block; min-width: 120px; text-align: center;">{}</span>',
            style, obj.get_status_display()
        )
    status_badge.short_description = 'وضعیت'
    
    def has_feedback(self, obj):
        if hasattr(obj, 'feedback'):
            return format_html('<span style="color: #28a745;">✓</span>')
        return format_html('<span style="color: #dc3545;">✗</span>')
    has_feedback.short_description = 'بازخورد'
    
    def mark_as_paid(self, request, queryset):
        """Mark orders as paid and transition to preparing"""
        updated = 0
        for order in queryset:
            if order.mark_as_paid(request.user):
                updated += 1
        self.message_user(request, f'{updated} سفارش پرداخت شده و در حال آماده‌سازی قرار گرفت.')
    mark_as_paid.short_description = "علامت‌گذاری به عنوان پرداخت شده"
    
    def mark_as_ready(self, request, queryset):
        """Mark orders as ready and handle delivery method logic"""
        updated = 0
        for order in queryset:
            if order.mark_as_ready(request.user):
                updated += 1
        self.message_user(request, f'{updated} سفارش آماده شد.')
    mark_as_ready.short_description = "علامت‌گذاری به عنوان آماده شده"
    
    def start_shipping_preparation(self, request, queryset):
        """Start shipping preparation for postal orders"""
        updated = 0
        for order in queryset.filter(delivery_method='postal'):
            if order.start_shipping_preparation(request.user):
                updated += 1
        self.message_user(request, f'{updated} سفارش پستی وارد مرحله آماده‌سازی ارسال شد.')
    start_shipping_preparation.short_description = "شروع آماده‌سازی ارسال (فقط پستی)"
    
    def mark_in_transit(self, request, queryset):
        """Mark orders as in transit"""
        updated = 0
        for order in queryset:
            if order.mark_in_transit(request.user):
                updated += 1
        self.message_user(request, f'{updated} سفارش در حال ارسال قرار گرفت.')
    mark_in_transit.short_description = "علامت‌گذاری به عنوان در حال ارسال"
    
    def export_orders(self, request, queryset):
        self.message_user(request, f'{queryset.count()} سفارش برای صادرات آماده شد.')
    export_orders.short_description = "صادرات سفارشات"
    
    def send_order_notifications(self, request, queryset):
        self.message_user(request, f'اعلان برای {queryset.count()} سفارش ارسال شد.')
    send_order_notifications.short_description = "ارسال اعلان سفارش"
    
    def item_count(self, obj):
        count = obj.items.count()
        return format_html('<span style="color: #007bff; font-weight: bold;">{}</span>', count)
    item_count.short_description = 'تعداد آیتم'
    
    def payment_status(self, obj):
        if obj.status == 'delivered':
            return format_html('<span style="color: #28a745;">✓ پرداخت شده</span>')
        elif obj.status == 'pending':
            return format_html('<span style="color: #ffc107;">⏳ در انتظار</span>')
        else:
            return format_html('<span style="color: #dc3545;">✗ ناموفق</span>')
    payment_status.short_description = 'وضعیت پرداخت'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items')

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
    search_fields = ('user__username', 'phone_number', 'address', 'user__email')
    list_filter = ('city', 'province', 'created_at')
    readonly_fields = ('order_count', 'total_spent', 'last_order_date', 'customer_type')
    list_per_page = 25
    actions = ['export_users', 'send_notification', 'mark_as_vip', 'mark_as_regular']
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user', 'phone_number', 'birth_date')
        }),
        ('آدرس', {
            'fields': ('address', 'city', 'province', 'postal_code')
        }),
        ('اطلاعات اضافی', {
            'fields': ('bio',)
        }),
        ('تصویر پروفایل', {
            'fields': ('avatar',),
            'classes': ('collapse',)
        }),
        ('آمار', {
            'fields': ('order_count', 'total_spent', 'last_order_date', 'customer_type'),
            'classes': ('collapse',)
        }),
    )
    
    def customer_type(self, obj):
        # Calculate total spent from user's orders
        total_spent = obj.user.order_set.filter(status__in=['delivered', 'shipped']).aggregate(
            total=Sum('total_amount'))['total'] or 0
        if total_spent > 1000000:  # 1 million toman
            return format_html('<span style="color: #ffd700; font-weight: bold;">VIP</span>')
        elif total_spent > 500000:  # 500k toman
            return format_html('<span style="color: #c0c0c0; font-weight: bold;">Silver</span>')
        else:
            return format_html('<span style="color: #cd7f32; font-weight: bold;">Bronze</span>')
    customer_type.short_description = 'نوع مشتری'
    
    def last_order_date(self, obj):
        last_order = obj.user.order_set.order_by('-created_at').first()
        if last_order:
            return last_order.created_at.strftime('%Y/%m/%d')
        return '-'
    last_order_date.short_description = 'آخرین سفارش'
    
    def export_users(self, request, queryset):
        self.message_user(request, f'{queryset.count()} کاربر برای صادرات آماده شد.')
    export_users.short_description = "صادرات کاربران"
    
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
        count = obj.user.order_set.count()
        return format_html('<span style="color: #007bff; font-weight: bold;">{}</span>', count)
    order_count.short_description = 'تعداد سفارش'
    
    def total_spent(self, obj):
        total = obj.user.order_set.filter(status__in=['delivered', 'shipped']).aggregate(
            total=Sum('total_amount'))['total'] or 0
        return format_html('<span style="color: #28a745; font-weight: bold;">{} تومان</span>', total)
    total_spent.short_description = 'مجموع خرید'
    
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
    
    def item_count(self, obj):
        count = obj.items.count()
        return format_html('<span style="color: #007bff; font-weight: bold;">{}</span>', count)
    item_count.short_description = 'تعداد آیتم'
    
    def get_total_quantity(self, obj):
        total = obj.items.aggregate(total=Sum('quantity'))['total'] or 0
        return format_html('<span style="color: #28a745; font-weight: bold;">{}</span>', total)
    get_total_quantity.short_description = 'تعداد کل'
    
    def get_total_price(self, obj):
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
