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
    GRIND_TYPE_CHOICES = [
        ('whole_bean', 'اسیاب نشده'),
        ('coarse', 'ترک'),
        ('medium_coarse', 'موکاپات'),
        ('medium', 'اسپرسو ساز نیمه صنعتی'),
        ('medium_fine', 'اسپرسوساز صنعتی'),
        ('fine', 'اسپرسوساز خانگی'),
    ]
    
    WEIGHT_CHOICES = [
        ('250g', '250 گرم'),
        ('500g', '500 گرم'),
        ('1kg', '1 کیلوگرم'),
        ('5kg', '5 کیلوگرم'),
        ('10kg', '10 کیلوگرم'),
    ]
    
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True)  # Base price for 250g
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, db_index=True)
    stock = models.IntegerField(default=0, db_index=True)
    featured = models.BooleanField(default=False, verbose_name='ویژه', db_index=True)
    available_grinds = models.JSONField(default=list, blank=True, help_text='Available grind types')
    available_weights = models.JSONField(default=list, blank=True, help_text='Available weight options')
    weight_multipliers = models.JSONField(default=dict, blank=True, help_text='Price multipliers for different weights')
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
    
    def get_price_for_weight(self, weight):
        """Get price for specific weight"""
        from decimal import Decimal
        multiplier = self.weight_multipliers.get(weight, 1.0)
        # Convert multiplier to Decimal to avoid float multiplication error
        if isinstance(multiplier, float):
            multiplier = Decimal(str(multiplier))
        return self.price * multiplier
    
    def get_available_grinds_display(self):
        """Get display names for available grinds"""
        grind_dict = dict(self.GRIND_TYPE_CHOICES)
        return [grind_dict.get(grind, grind) for grind in self.available_grinds]
    
    def get_available_weights_display(self):
        """Get display names for available weights"""
        weight_dict = dict(self.WEIGHT_CHOICES)
        return [weight_dict.get(weight, weight) for weight in self.available_weights]

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
    grind_type = models.CharField(max_length=20, choices=Product.GRIND_TYPE_CHOICES, default='whole_bean')
    weight = models.CharField(max_length=10, choices=Product.WEIGHT_CHOICES, default='250g')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product', 'grind_type', 'weight')

    def __str__(self):
        grind_display = dict(Product.GRIND_TYPE_CHOICES).get(self.grind_type, self.grind_type)
        weight_display = dict(Product.WEIGHT_CHOICES).get(self.weight, self.weight)
        return f"{self.quantity}x {self.product.name} - {grind_display} - {weight_display}"

    def get_unit_price(self):
        """Get price per unit with weight multiplier"""
        return self.product.get_price_for_weight(self.weight)

    def get_total_price(self):
        return self.get_unit_price() * self.quantity

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending_payment', 'در انتظار پرداخت'),
        ('preparing', 'در حال آمــاده‌سازی'),
        ('ready', 'آماده شده'),
        ('shipping_preparation', 'در حال ارسال به اداره پست'),
        ('in_transit', 'بسته در حال رسیدن به مقصد است'),
        ('pickup_ready', 'آماده شده است و لطفاً مراجعه کنید'),
    ]
    
    DELIVERY_CHOICES = [
        ('pickup', 'دریافت حضوری'),
        ('postal', 'ارسال پستی'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending_payment')
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
    
    def can_transition_to(self, new_status):
        """Check if the order can transition to the given status"""
        valid_transitions = {
            'pending_payment': ['preparing'],
            'preparing': ['ready'],
            'ready': ['shipping_preparation', 'pickup_ready'],
            'shipping_preparation': ['in_transit'],
            'in_transit': [],
            'pickup_ready': [],
        }
        return new_status in valid_transitions.get(self.status, [])
    
    def transition_to(self, new_status, user=None):
        """Transition the order to a new status with validation"""
        if not self.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status} to {new_status}")
        
        old_status = self.status
        self.status = new_status
        self.save()
        
        # Create notification for the customer
        from .models import Notification
        Notification.create_notification(
            user=self.user,
            notification_type='order_status',
            title=f'تغییر وضعیت سفارش #{self.id}',
            message=f'وضعیت سفارش شما از "{dict(self.STATUS_CHOICES)[old_status]}" به "{dict(self.STATUS_CHOICES)[new_status]}" تغییر کرد.',
            related_object=self
        )
        
        return True
    
    def mark_as_paid(self, user=None):
        """Mark order as paid and automatically transition to preparing"""
        if self.status == 'pending_payment':
            return self.transition_to('preparing', user)
        return False
    
    def mark_as_ready(self, user=None):
        """Mark order as ready and handle delivery method logic"""
        if self.status == 'preparing':
            if self.transition_to('ready', user):
                # Auto-transition based on delivery method
                if self.delivery_method == 'pickup':
                    return self.transition_to('pickup_ready', user)
                return True
        return False
    
    def start_shipping_preparation(self, user=None):
        """Start shipping preparation for postal orders"""
        if self.status == 'ready' and self.delivery_method == 'postal':
            return self.transition_to('shipping_preparation', user)
        return False
    
    def mark_in_transit(self, user=None):
        """Mark order as in transit"""
        if self.status == 'shipping_preparation':
            return self.transition_to('in_transit', user)
        return False
    
    def get_status_badge_color(self):
        """Get the appropriate color for status badge"""
        status_colors = {
            'pending_payment': '#8B4513',  # Coffee brown
            'preparing': '#D2691E',       # Chocolate brown  
            'ready': '#CD853F',           # Peru brown
            'shipping_preparation': '#A0522D',  # Sienna
            'in_transit': '#654321',      # Dark brown
            'pickup_ready': '#228B22',    # Forest green
        }
        return status_colors.get(self.status, '#8B4513')

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
    """Extended user profile with additional information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, verbose_name='شماره تلفن')
    birth_date = models.DateField(null=True, blank=True, verbose_name='تاریخ تولد')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='عکس پروفایل')
    bio = models.TextField(max_length=500, blank=True, verbose_name='درباره من')
    city = models.CharField(max_length=100, blank=True, verbose_name='شهر')
    province = models.CharField(max_length=100, blank=True, verbose_name='استان')
    address = models.TextField(blank=True, verbose_name='آدرس')
    postal_code = models.CharField(max_length=10, blank=True, verbose_name='کد پستی')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'پروفایل کاربر'
        verbose_name_plural = 'پروفایل‌های کاربران'
    
    def __str__(self):
        return f"پروفایل {self.user.username}"

class UserAddress(models.Model):
    """Multiple addresses for each user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    title = models.CharField(max_length=100, verbose_name='عنوان آدرس')  # e.g., "خانه", "محل کار"
    full_address = models.TextField(verbose_name='آدرس کامل')
    city = models.CharField(max_length=100, verbose_name='شهر')
    state = models.CharField(max_length=100, verbose_name='استان')
    is_default = models.BooleanField(default=False, verbose_name='آدرس پیش‌فرض')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'آدرس کاربر'
        verbose_name_plural = 'آدرس‌های کاربران'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            UserAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

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

# ===== PHASE 3: ADVANCED FEATURES MODELS =====

class UserActivity(models.Model):
    """Track user behavior for AI recommendations and analytics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    page = models.CharField(max_length=200)
    action = models.CharField(max_length=100)  # view, like, add_to_cart, purchase, search
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    session_duration = models.IntegerField(default=0)  # in seconds
    device_type = models.CharField(max_length=20, default='desktop')  # desktop, mobile, tablet
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['product', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"

class ProductRecommendation(models.Model):
    """Store AI-generated recommendations for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)  # Recommendation confidence score
    reason = models.CharField(max_length=200, blank=True)  # Why this was recommended
    recommendation_type = models.CharField(max_length=50, default='similar')  # similar, collaborative, trending
    is_viewed = models.BooleanField(default=False)
    is_purchased = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-score', '-created_at']
        indexes = [
            models.Index(fields=['user', '-score']),
            models.Index(fields=['recommendation_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} → {self.product.name} ({self.score:.2f})"

class CustomerSegment(models.Model):
    """Customer segmentation for targeted marketing and analytics"""
    SEGMENT_CHOICES = [
        ('vip', 'مشتری VIP'),
        ('regular', 'مشتری عادی'),
        ('new', 'مشتری جدید'),
        ('inactive', 'غیرفعال'),
        ('coffee_enthusiast', 'علاقه‌مند به قهوه'),
        ('dessert_lover', 'علاقه‌مند به دسر'),
        ('price_sensitive', 'حساس به قیمت'),
        ('premium_buyer', 'خریدار لوکس'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='segment')
    segment_type = models.CharField(max_length=20, choices=SEGMENT_CHOICES, default='new')
    total_spent = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    order_count = models.IntegerField(default=0)
    last_order_date = models.DateTimeField(null=True, blank=True)
    favorite_categories = models.JSONField(default=list)  # List of category IDs
    average_order_value = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    engagement_score = models.FloatField(default=0.0)  # Based on activity frequency
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['segment_type']),
            models.Index(fields=['total_spent']),
            models.Index(fields=['engagement_score']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_segment_type_display()}"

class LoyaltyProgram(models.Model):
    """Loyalty program with points and tiers"""
    TIER_CHOICES = [
        ('bronze', 'برنزی'),
        ('silver', 'نقره‌ای'),
        ('gold', 'طلایی'),
        ('platinum', 'پلاتینیوم'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty')
    points = models.IntegerField(default=0)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='bronze')
    total_earned_points = models.IntegerField(default=0)
    total_redeemed_points = models.IntegerField(default=0)
    tier_achieved_date = models.DateTimeField(auto_now_add=True)
    next_tier_points_needed = models.IntegerField(default=500)
    
    class Meta:
        indexes = [
            models.Index(fields=['tier', '-points']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_tier_display()} ({self.points} امتیاز)"
    
    def calculate_tier(self):
        """Calculate tier based on total spent"""
        segment = getattr(self.user, 'segment', None)
        if not segment:
            return 'bronze'
            
        total_spent = segment.total_spent
        if total_spent >= 5000000:  # 5M toman
            return 'platinum'
        elif total_spent >= 2000000:  # 2M toman
            return 'gold'
        elif total_spent >= 500000:  # 500K toman
            return 'silver'
        else:
            return 'bronze'
    
    def get_tier_benefits(self):
        """Get tier-specific benefits"""
        benefits = {
            'bronze': {'discount': 5, 'min_order': 200000, 'free_shipping': False},
            'silver': {'discount': 10, 'min_order': 150000, 'free_shipping': True},
            'gold': {'discount': 15, 'min_order': 100000, 'free_shipping': True, 'priority': True},
            'platinum': {'discount': 20, 'min_order': 0, 'free_shipping': True, 'priority': True, 'vip': True}
        }
        return benefits.get(self.tier, benefits['bronze'])

class SearchQuery(models.Model):
    """Track search queries for analytics and optimization"""
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    query = models.CharField(max_length=200)
    results_count = models.IntegerField(default=0)
    clicked_product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    filters_used = models.JSONField(default=dict)  # Store applied filters
    timestamp = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=40, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['query', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
    
    def __str__(self):
        return f"'{self.query}' - {self.results_count} نتیجه"

class ProductInteraction(models.Model):
    """Track specific product interactions for recommendations"""
    INTERACTION_TYPES = [
        ('view', 'مشاهده'),
        ('like', 'پسندیدن'),
        ('favorite', 'علاقه‌مندی'),
        ('cart_add', 'افزودن به سبد'),
        ('purchase', 'خرید'),
        ('review', 'نظردهی'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_interactions')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=40, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'interaction_type', '-timestamp']),
            models.Index(fields=['product', 'interaction_type', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_interaction_type_display()} - {self.product.name}"
