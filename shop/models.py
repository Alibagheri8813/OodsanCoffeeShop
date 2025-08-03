from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, db_index=True)
    stock = models.IntegerField(default=0, db_index=True)
    featured = models.BooleanField(default=False, verbose_name='ویژه', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['featured', '-created_at']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"سبد خرید {self.user.username}"

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_quantity(self):
        return sum(item.quantity for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    def get_total_price(self):
        return self.product.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('processing', 'در حال پردازش'),
        ('shipped', 'ارسال شده'),
        ('delivered', 'تحویل داده شده'),
        ('cancelled', 'لغو شده'),
    ]
    
    DELIVERY_CHOICES = [
        ('pickup', 'دریافت حضوری'),
        ('post', 'ارسال پستی'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='pickup')
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipping_address = models.TextField(default='')
    postal_code = models.CharField(max_length=10, default='')
    phone_number = models.CharField(max_length=15, default='')
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"سفارش {self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

class OrderFeedback(models.Model):
    RATING_CHOICES = [
        (1, 'خیلی بد'),
        (2, 'بد'),
        (3, 'متوسط'),
        (4, 'خوب'),
        (5, 'عالی'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='feedback')
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name='امتیاز')
    comment = models.TextField(verbose_name='نظر', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'بازخورد سفارش'
        verbose_name_plural = 'بازخوردهای سفارش'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"بازخورد سفارش {self.order.id} - امتیاز: {self.rating}"

class Comment(models.Model):
    product = models.ForeignKey(Product, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"نظر {self.user.username} برای {self.product.name}"

class ProductLike(models.Model):
    product = models.ForeignKey(Product, related_name='likes', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('product', 'user')

    def __str__(self):
        return f"پسندیدن {self.product.name} توسط {self.user.username}"

class ProductFavorite(models.Model):
    product = models.ForeignKey(Product, related_name='favorites', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"محصول مورد علاقه {self.product.name} برای {self.user.username}"

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    city = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)
    national_code = models.CharField(max_length=10, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"پروفایل {self.user.username}"

    def get_full_address(self):
        """Returns formatted full address"""
        parts = []
        if self.address:
            parts.append(self.address)
        if self.city:
            parts.append(self.city)
        if self.province:
            parts.append(self.province)
        if self.postal_code:
            parts.append(f"کد پستی: {self.postal_code}")
        return "، ".join(parts) if parts else "آدرس ثبت نشده"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('order_new', 'سفارش جدید'),
        ('order_status', 'تغییر وضعیت سفارش'),
        ('low_stock', 'موجودی کم'),
        ('feedback_new', 'بازخورد جدید'),
        ('user_new', 'کاربر جدید'),
        ('system', 'سیستم'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()
    
    @classmethod
    def create_notification(cls, user, notification_type, title, message, related_object=None):
        """Create a notification for a user"""
        notification = cls.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message
        )
        
        if related_object:
            notification.related_object_id = related_object.id
            notification.related_object_type = related_object.__class__.__name__
            notification.save()
        
        return notification
    
    @classmethod
    def create_admin_notification(cls, notification_type, title, message, related_object=None):
        """Create notifications for all admin users"""
        admin_users = User.objects.filter(is_staff=True)
        notifications = []
        
        for user in admin_users:
            notification = cls.create_notification(user, notification_type, title, message, related_object)
            notifications.append(notification)
        
        return notifications

class Video(models.Model):
    title = models.CharField(max_length=200, verbose_name='عنوان')
    video_file = models.FileField(upload_to='videos/', verbose_name='فایل ویدیو')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'ویدیو'
        verbose_name_plural = 'ویدیوها'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class UserActivity(models.Model):
    """Track user behavior for AI recommendations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    page = models.CharField(max_length=200)
    action = models.CharField(max_length=100)  # view, like, favorite, purchase
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    session_duration = models.IntegerField(default=0)  # seconds
    device_type = models.CharField(max_length=20, default='desktop')  # mobile, desktop, tablet
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"

class ProductRecommendation(models.Model):
    """AI-powered product recommendations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recommendations')
    score = models.FloatField(default=0.0)  # AI recommendation score
    reason = models.CharField(max_length=200, blank=True)  # Why recommended
    is_viewed = models.BooleanField(default=False)
    is_purchased = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-score']
        unique_together = ('user', 'product')
    
    def __str__(self):
        return f"Recommendation for {self.user.username}: {self.product.name} (Score: {self.score})"

class SearchQuery(models.Model):
    """Track search queries for analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    query = models.CharField(max_length=500)
    results_count = models.IntegerField(default=0)
    filters_applied = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Search: {self.query} ({self.results_count} results)"

class CustomerSegment(models.Model):
    """Customer segmentation for targeted marketing"""
    SEGMENT_CHOICES = [
        ('vip', 'VIP'),
        ('regular', 'Regular'),
        ('new', 'New'),
        ('inactive', 'Inactive'),
        ('high_value', 'High Value'),
        ('coffee_enthusiast', 'Coffee Enthusiast'),
        ('dessert_lover', 'Dessert Lover'),
        ('casual', 'Casual'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='segment')
    segment_type = models.CharField(max_length=20, choices=SEGMENT_CHOICES, default='new')
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    order_count = models.IntegerField(default=0)
    last_order_date = models.DateTimeField(null=True, blank=True)
    favorite_categories = models.JSONField(default=list)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-total_spent']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_segment_type_display()}"

class AnalyticsEvent(models.Model):
    """Track business analytics events"""
    EVENT_TYPES = [
        ('page_view', 'Page View'),
        ('product_view', 'Product View'),
        ('add_to_cart', 'Add to Cart'),
        ('purchase', 'Purchase'),
        ('search', 'Search'),
        ('filter', 'Filter'),
        ('recommendation_click', 'Recommendation Click'),
        ('review_submit', 'Review Submit'),
        ('favorite_add', 'Add to Favorites'),
        ('like_product', 'Like Product'),
    ]
    
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    metadata = models.JSONField(default=dict)  # Additional event data
    timestamp = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.timestamp}"

class PushSubscription(models.Model):
    """Push notification subscriptions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    subscription_data = models.JSONField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Push subscription for {self.user.username}"

class LoyaltyProgram(models.Model):
    """Loyalty program for customers"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty')
    points = models.IntegerField(default=0)
    tier = models.CharField(max_length=20, default='bronze')  # bronze, silver, gold, platinum
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    points_earned = models.IntegerField(default=0)
    points_redeemed = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-points']
    
    def __str__(self):
        return f"{self.user.username} - {self.tier} ({self.points} points)"
    
    def calculate_tier(self):
        """Calculate loyalty tier based on total spent"""
        if self.total_spent >= 5000000:  # 5M toman
            return 'platinum'
        elif self.total_spent >= 2000000:  # 2M toman
            return 'gold'
        elif self.total_spent >= 500000:  # 500K toman
            return 'silver'
        else:
            return 'bronze'
    
    def add_points(self, amount):
        """Add points to loyalty account"""
        self.points += amount
        self.points_earned += amount
        self.tier = self.calculate_tier()
        self.save()
    
    def redeem_points(self, amount):
        """Redeem points"""
        if self.points >= amount:
            self.points -= amount
            self.points_redeemed += amount
            self.save()
            return True
        return False
