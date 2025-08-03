from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from .forms import UserRegistrationForm, CheckoutForm 
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from .models import *
from .forms import *
import json
import logging

# Get logger for this module
logger = logging.getLogger(__name__)

# Create your views here.

def home(request):
    """Home page view with enhanced error handling"""
    try:
        categories = Category.objects.filter(parent__isnull=True)
    except Exception as e:
        logger.error(f"Error loading categories in home view: {e}")
        categories = Category.objects.none()
    
    try:
        return render(request, 'shop/home.html', {'categories': categories})
    except RecursionError as e:
        logger.error(f"Template recursion error in home view: {e}")
        # Return a simple error page to avoid template recursion
        from django.http import HttpResponse
        return HttpResponse("""
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <title>خطای سیستم</title>
            <meta charset="utf-8">
            <style>
                body { font-family: 'Vazirmatn', Arial, sans-serif; text-align: center; margin: 50px; }
                .error { background: #f8d7da; color: #721c24; padding: 30px; border-radius: 10px; }
            </style>
        </head>
        <body>
            <div class="error">
                <h1>⚠️ خطای سیستم</h1>
                <p>متأسفانه خطای بازگشت بی‌نهایت شناسایی شد.</p>
                <p><strong>مسیر مشکل‌دار:</strong> /home/</p>
                <p>این خطا به دلیل مشکل در قالب‌ها ایجاد شده است.</p>
                <a href="/shop/" style="display: inline-block; background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">رفتن به فروشگاه</a>
            </div>
        </body>
        </html>
        """, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in home view: {e}")
        from django.http import HttpResponse
        return HttpResponse("خطای سیستمی رخ داده است. لطفاً بعداً تلاش کنید.", status=500)

def video_intro(request):
    """Video intro page that shows for 6 seconds then redirects to home"""
    from django.utils import timezone
    timestamp = int(timezone.now().timestamp())
    return render(request, 'shop/video_intro.html', {'timestamp': timestamp})

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'خوش آمدید {username}!')
                return redirect('home')
            else:
                messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
        else:
            messages.error(request, 'لطفاً اطلاعات را به درستی وارد کنید.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'shop/login.html', {'form': form})

def signup(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Create user profile
                UserProfile.objects.create(user=user)
                # Create welcome notification
                Notification.objects.create(
                    user=user,
                    notification_type='system',
                    title='خوش آمدید!',
                    message='به کافی شاپ خوش آمدید! لطفاً پروفایل خود را تکمیل کنید.'
                )
                messages.success(request, 'حساب کاربری با موفقیت ایجاد شد. لطفاً وارد شوید.')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'خطا در ایجاد حساب کاربری: {str(e)}')
        else:
            # Add specific error messages for common validation issues
            if 'username' in form.errors:
                if 'unique' in str(form.errors['username']):
                    messages.error(request, 'این نام کاربری قبلاً استفاده شده است.')
                elif 'min_length' in str(form.errors['username']):
                    messages.error(request, 'نام کاربری باید حداقل 3 کاراکتر باشد.')
            if 'password2' in form.errors:
                if 'password_mismatch' in str(form.errors['password2']):
                    messages.error(request, 'رمز عبور و تکرار آن مطابقت ندارند.')
            if 'password1' in form.errors:
                if 'too_short' in str(form.errors['password1']):
                    messages.error(request, 'رمز عبور باید حداقل 8 کاراکتر باشد.')
                elif 'too_common' in str(form.errors['password1']):
                    messages.error(request, 'رمز عبور خیلی ساده است.')
    else:
        form = UserCreationForm()
    
    return render(request, 'shop/signup.html', {'form': form})

def custom_logout(request):
    logout(request)
    messages.success(request, 'شما با موفقیت خارج شدید.')
    return redirect('home')

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'shop/category_list.html', {'categories': categories})

def category_detail(request, category_id):
    category = Category.objects.get(id=category_id)
    subcategories = Category.objects.filter(parent=category)
    products = Product.objects.filter(category=category)
    return render(request, 'shop/category_detail.html', {
        'category': category,
        'subcategories': subcategories,
        'products': products,
    })

def product_detail(request, product_id):
    """Display detailed information for a specific product"""
    product = get_object_or_404(Product, id=product_id)
    comments = Comment.objects.filter(product=product).order_by('-created_at')
    
    # Get like count and user like status
    like_count = ProductLike.objects.filter(product=product).count()
    user_liked = False
    if request.user.is_authenticated:
        user_liked = ProductLike.objects.filter(product=product, user=request.user).exists()
    
    # Check if product is in user's favorites
    user_favorites = set()
    if request.user.is_authenticated:
        user_favorites = set(ProductFavorite.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True))
    
    # Handle POST requests for comments and likes
    if request.method == 'POST':
        if 'text' in request.POST and request.user.is_authenticated:
            text = request.POST.get('text')
            if text.strip():
                Comment.objects.create(
                    product=product,
                    user=request.user,
                    text=text
                )
                messages.success(request, 'نظر شما با موفقیت ثبت شد.')
                return redirect('product_detail', product_id=product_id)
        
        elif 'like_submit' in request.POST and request.user.is_authenticated:
            like, created = ProductLike.objects.get_or_create(
                product=product,
                user=request.user
            )
            if not created:
                like.delete()
            return redirect('product_detail', product_id=product_id)
    
    context = {
        'product': product,
        'comments': comments,
        'reviews': comments,  # For template compatibility
        'like_count': like_count,
        'total_likes': like_count,
        'total_favorites': product.favorites.count(),
        'total_reviews': comments.count(),
        'user_liked': user_liked,
        'user_favorites': user_favorites,
    }
    return render(request, 'shop/product_detail.html', context)

@login_required
@require_POST
def add_to_favorites(request, product_id):
    """Add a product to user's favorites"""
    product = get_object_or_404(Product, id=product_id)
    favorite, created = ProductFavorite.objects.get_or_create(
        product=product,
        user=request.user
    )
    
    if created:
        # Create notification for adding to favorites
        Notification.objects.create(
            user=request.user,
            notification_type='favorite_added',
            title='محصول به علاقه‌مندی‌ها اضافه شد',
            message=f'محصول "{product.name}" به لیست علاقه‌مندی‌های شما اضافه شد.'
        )
        return JsonResponse({'status': 'added', 'message': 'محصول به علاقه‌مندی‌ها اضافه شد'})
    else:
        return JsonResponse({'status': 'exists', 'message': 'این محصول قبلاً در علاقه‌مندی‌های شما موجود است'})

@login_required
@require_POST
def remove_from_favorites(request, product_id):
    """Remove a product from user's favorites"""
    product = get_object_or_404(Product, id=product_id)
    try:
        favorite = ProductFavorite.objects.get(product=product, user=request.user)
        favorite.delete()
        return JsonResponse({'status': 'removed', 'message': 'محصول از علاقه‌مندی‌ها حذف شد'})
    except ProductFavorite.DoesNotExist:
        return JsonResponse({'status': 'not_found', 'message': 'این محصول در علاقه‌مندی‌های شما موجود نیست'})

@login_required
def favorite_products(request):
    """Display user's favorite products"""
    favorites = ProductFavorite.objects.filter(user=request.user).select_related('product')
    products = [favorite.product for favorite in favorites]
    
    context = {
        'products': products,
        'page_title': 'محصولات مورد علاقه',
        'is_favorites_page': True
    }
    return render(request, 'shop/favorite_products.html', context)

from django.core.cache import cache
from django.views.decorators.cache import cache_page

def product_list(request, category_id=None):
    """Enhanced product list with better search, filters, and pagination - SINGLE UNIFIED VERSION"""
    # Safe category loading to prevent recursion
    try:
        categories = Category.objects.filter(parent=None).select_related('parent')
        # Don't use prefetch_related to avoid potential circular reference issues
    except Exception as e:
        logger.error(f"Error loading categories: {e}")
        categories = Category.objects.none()
    
    # Optimize product queries with select_related and prefetch_related
    products = Product.objects.select_related('category').prefetch_related('likes', 'favorites')
    
    # Category filter (support both URL parameter and GET parameter)
    if category_id:
        category = get_object_or_404(Category, id=category_id)
        products = products.filter(category=category)
    elif request.GET.get('category'):
        try:
            cat_id = int(request.GET.get('category'))
            products = products.filter(category_id=cat_id)
        except (ValueError, TypeError):
            pass
    
    # Enhanced search with database indexes (support both 'q' and 'search' parameters)
    query = request.GET.get('q', '') or request.GET.get('search', '')
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
    
    # Price filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            products = products.filter(price__gte=int(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=int(max_price))
        except ValueError:
            pass
    
    # Sort options with optimized ordering
    sort_by = request.GET.get('sort', 'featured')
    if sort_by == 'price_low':
        products = products.order_by('price', 'name')
    elif sort_by == 'price_high':
        products = products.order_by('-price', 'name')
    elif sort_by == 'newest':
        products = products.order_by('-created_at', 'name')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'popular':
        products = products.annotate(like_count=Count('likes')).order_by('-like_count', 'name')
    else:  # default: featured first
        products = products.order_by('-featured', '-created_at', 'name')
    
    # Add pagination
    from django.core.paginator import Paginator
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Check if products are in user's favorites
    user_favorites = set()
    if request.user.is_authenticated:
        user_favorites = set(ProductFavorite.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True))
    
    context = {
        'products': page_obj,  # Use paginated products
        'categories': categories,
        'query': query,
        'search_query': query,  # Support both variable names
        'selected_category': category_id or request.GET.get('category'),
        'user_favorites': user_favorites,
        'sort_options': [
            ('featured', 'پیشنهادی'),
            ('name', 'نام'),
            ('price_low', 'قیمت: کم به زیاد'),
            ('price_high', 'قیمت: زیاد به کم'),
            ('newest', 'جدیدترین'),
            ('popular', 'محبوب‌ترین')
        ],
        'current_sort': sort_by,
        'sort_by': sort_by,  # Support both variable names
        'min_price': min_price,
        'max_price': max_price
    }
    return render(request, 'shop/product_list.html', context)

@login_required
def user_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Check if any data actually changed to avoid unnecessary notifications
        old_phone = profile.phone_number
        old_address = profile.address
        old_postal = profile.postal_code
        old_city = profile.city
        old_province = profile.province
        old_national = profile.national_code
        
        # Update all profile information in one go
        profile.phone_number = request.POST.get('phone_number', '')
        profile.address = request.POST.get('address', '')
        profile.postal_code = request.POST.get('postal_code', '')
        profile.city = request.POST.get('city', '')
        profile.province = request.POST.get('province', '')
        profile.national_code = request.POST.get('national_code', '')
        
        # Handle birth date
        birth_date_str = request.POST.get('birth_date', '')
        if birth_date_str:
            try:
                profile.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Handle profile image
        if 'profile_image' in request.FILES:
            profile.profile_image = request.FILES['profile_image']
        
        profile.save()
        
        # Only create notification if significant data changed
        data_changed = (
            old_phone != profile.phone_number or
            old_address != profile.address or
            old_postal != profile.postal_code or
            old_city != profile.city or
            old_province != profile.province or
            old_national != profile.national_code
        )
        
        if data_changed:
            # Create notification for profile update
            Notification.objects.create(
                user=request.user,
                notification_type='profile_update',
                title='پروفایل بروزرسانی شد',
                message='اطلاعات پروفایل شما با موفقیت بروزرسانی شد.'
            )
        
        messages.success(request, 'پروفایل شما با موفقیت بروزرسانی شد.')
        return redirect('user_profile')
    
    # Get user's orders
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Get unread notifications count
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    
    # Dashboard statistics
    favorite_count = ProductFavorite.objects.filter(user=request.user).count()
    total_spent = sum(order.total_amount for order in orders if order.status in ['paid', 'processing', 'shipped', 'delivered'])
    completed_orders = orders.filter(status='delivered').count()
    
    # Get user's favorite products
    user_favorites = ProductFavorite.objects.filter(user=request.user).select_related('product')[:6]
    
    # Get recent activities (orders, notifications, favorites)
    recent_activities = []
    
    # Add recent orders
    for order in orders[:3]:
        recent_activities.append({
            'type': 'order',
            'title': f'سفارش #{order.id} ثبت شد',
            'time': order.created_at
        })
    
    # Add recent notifications
    recent_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:3]
    for notification in recent_notifications:
        recent_activities.append({
            'type': 'notification',
            'title': notification.title,
            'time': notification.created_at
        })
    
    # Add recent favorites
    recent_favorites = ProductFavorite.objects.filter(user=request.user).select_related('product').order_by('-created_at')[:3]
    for favorite in recent_favorites:
        recent_activities.append({
            'type': 'favorite',
            'title': f'"{favorite.product.name}" به علاقه‌مندی‌ها اضافه شد',
            'time': favorite.created_at
        })
    
    # Sort activities by time (most recent first)
    recent_activities.sort(key=lambda x: x['time'], reverse=True)
    recent_activities = recent_activities[:5]  # Limit to 5 most recent activities
    
    return render(request, 'shop/user_profile.html', {
        'profile': profile,
        'orders': orders,
        'unread_notifications': unread_notifications,
        'favorite_count': favorite_count,
        'total_spent': total_spent,
        'completed_orders': completed_orders,
        'user_favorites': user_favorites,
        'recent_activities': recent_activities
    })

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/order_history.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Check if feedback already exists
    feedback = None
    if hasattr(order, 'feedback'):
        feedback = order.feedback
    
    return render(request, 'shop/order_detail.html', {
        'order': order,
        'profile': request.user.profile,
        'feedback': feedback
    })

@login_required
@require_POST
def submit_order_feedback(request, order_id):
    """Submit feedback for a delivered order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Only allow feedback for delivered orders
    if order.status != 'delivered':
        return JsonResponse({'success': False, 'message': 'فقط برای سفارشات تحویل شده می‌توانید بازخورد ارسال کنید'})
    
    # Check if feedback already exists
    if hasattr(order, 'feedback'):
        return JsonResponse({'success': False, 'message': 'شما قبلاً برای این سفارش بازخورد ارسال کرده‌اید'})
    
    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '')
    
    if not rating:
        return JsonResponse({'success': False, 'message': 'لطفاً امتیاز خود را انتخاب کنید'})
    
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return JsonResponse({'success': False, 'message': 'امتیاز باید بین 1 تا 5 باشد'})
    except ValueError:
        return JsonResponse({'success': False, 'message': 'امتیاز نامعتبر است'})
    
    # Create feedback
    from .models import OrderFeedback
    feedback = OrderFeedback.objects.create(
        order=order,
        rating=rating,
        comment=comment
    )
    
    # Create notification for admin users
    admin_users = User.objects.filter(is_staff=True)
    for admin_user in admin_users:
        Notification.objects.create(
            user=admin_user,
            notification_type='feedback_new',
            title=f'بازخورد جدید برای سفارش #{order.id}',
            message=f'بازخورد جدید از {request.user.username} با امتیاز {rating} ستاره برای سفارش #{order.id}',
            related_object_id=feedback.id,
            related_object_type='OrderFeedback'
        )
    
    messages.success(request, 'بازخورد شما با موفقیت ثبت شد. از شما متشکریم!')
    return JsonResponse({'success': True, 'message': 'بازخورد شما با موفقیت ثبت شد'})

@login_required
def notifications(request):
    notifications_list = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/notifications.html', {'notifications': notifications_list})

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False}, status=404)

@login_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

@login_required
@require_POST
def delete_notification(request, notification_id):
    """Delete a notification"""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.delete()
        return JsonResponse({'success': True, 'message': 'اعلان با موفقیت حذف شد'})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'اعلان یافت نشد'}, status=404)

@login_required
def address_completion_check(request):
    """Check if user has completed their address information"""
    try:
        profile = request.user.profile
        # Check if all required address fields are filled
        has_complete_address = bool(
            profile.address and 
            profile.address.strip() and
            profile.postal_code and 
            profile.postal_code.strip() and
            profile.city and 
            profile.city.strip() and
            profile.province and 
            profile.province.strip()
        )
        return JsonResponse({'has_complete_address': has_complete_address})
    except UserProfile.DoesNotExist:
        return JsonResponse({'has_complete_address': False})

@login_required
@require_POST
def like_product(request, product_id):
    """Like a product"""
    product = get_object_or_404(Product, id=product_id)
    like, created = ProductLike.objects.get_or_create(
        product=product,
        user=request.user
    )
    
    like_count = ProductLike.objects.filter(product=product).count()
    return JsonResponse({
        'status': 'liked',
        'like_count': like_count
    })

@login_required
@require_POST
def unlike_product(request, product_id):
    """Unlike a product"""
    product = get_object_or_404(Product, id=product_id)
    try:
        like = ProductLike.objects.get(product=product, user=request.user)
        like.delete()
        like_count = ProductLike.objects.filter(product=product).count()
        return JsonResponse({
            'status': 'unliked',
            'like_count': like_count
        })
    except ProductLike.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Like not found'}, status=404)

@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update session to prevent logout
            update_session_auth_hash(request, form.user)
            messages.success(request, 'رمز عبور شما با موفقیت تغییر یافت.')
            return redirect('user_profile')
        else:
            messages.error(request, 'لطفاً اطلاعات را به درستی وارد کنید.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'shop/change_password.html', {'form': form})

# Cart Views
@login_required
def cart_view(request):
    """Display user's cart"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    

    
    # Check if user has completed address information
    try:
        profile = request.user.profile
        has_complete_address = bool(
            profile.address and 
            profile.address.strip() and
            profile.postal_code and 
            profile.postal_code.strip() and
            profile.city and 
            profile.city.strip() and
            profile.province and 
            profile.province.strip() and
            profile.phone_number and
            profile.phone_number.strip()
        )
    except UserProfile.DoesNotExist:
        has_complete_address = False
    
    return render(request, 'shop/cart.html', {
        'cart': cart,
        'cart_items': cart.items.all(),
        'subtotal': cart.get_total_price(),
        'delivery_fee': 50000 if cart.get_total_price() < 500000 else 0,
        'total': cart.get_total_price() + (50000 if cart.get_total_price() < 500000 else 0),
        'is_cart_empty': cart.items.count() == 0,
        'has_complete_address': has_complete_address
    })

# ===== SENSATIONAL SHOPPING CART SYSTEM =====

@login_required
def add_to_cart(request):
    """Add product to cart with AJAX support"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
            
            product = get_object_or_404(Product, id=product_id)
            
            # Check stock availability
            if product.stock < quantity:
                return JsonResponse({
                    'success': False,
                    'message': f'موجودی کافی نیست. فقط {product.stock} عدد موجود است.',
                    'available_stock': product.stock
                })
            
            # Get or create cart
            cart, created = Cart.objects.get_or_create(user=request.user)
            
            # Get or create cart item
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                # Update quantity if item already exists
                cart_item.quantity += quantity
                cart_item.save()
            
            # Update product stock
            product.stock -= quantity
            product.save()
            
            # Calculate cart totals
            cart_total = cart.get_total_price()
            cart_count = cart.get_total_quantity()
            

            
            return JsonResponse({
                'success': True,
                'message': f'{product.name} به سبد خرید اضافه شد!',
                'cart_total': cart_total,
                'cart_count': cart_count,
                'product_name': product.name,
                'product_image': product.image.url if product.image else None
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در افزودن به سبد خرید: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'درخواست نامعتبر'})

@login_required
def update_cart_item(request):
    """Update cart item quantity with AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            quantity = int(data.get('quantity', 1))
            
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            product = cart_item.product
            
            if quantity <= 0:
                # Remove item if quantity is 0 or negative
                cart_item.delete()
                # Restore stock
                product.stock += cart_item.quantity
                product.save()
            else:
                # Check if we have enough stock
                available_stock = product.stock + cart_item.quantity
                if available_stock < quantity:
                    return JsonResponse({
                        'success': False,
                        'message': f'موجودی کافی نیست. فقط {available_stock} عدد موجود است.',
                        'available_stock': available_stock
                    })
                
                # Update stock
                product.stock = available_stock - quantity
                product.save()
                
                # Update cart item
                cart_item.quantity = quantity
                cart_item.save()
            
            # Calculate new totals
            cart = request.user.cart
            cart_total = cart.get_total_price()
            cart_count = cart.get_total_quantity()
            
            return JsonResponse({
                'success': True,
                'cart_total': cart_total,
                'cart_count': cart_count,
                'item_total': cart_item.get_total_price() if quantity > 0 else 0
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در به‌روزرسانی سبد خرید: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'درخواست نامعتبر'})

@login_required
def remove_from_cart(request):
    """Remove item from cart with AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            product = cart_item.product
            
            # Restore stock
            product.stock += cart_item.quantity
            product.save()
            
            # Remove item
            cart_item.delete()
            
            # Calculate new totals
            cart = request.user.cart
            cart_total = cart.get_total_price()
            cart_count = cart.get_total_quantity()
            
            return JsonResponse({
                'success': True,
                'message': 'محصول از سبد خرید حذف شد',
                'cart_total': cart_total,
                'cart_count': cart_count
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'خطا در حذف از سبد خرید: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'درخواست نامعتبر'})

@login_required
def cart_count(request):
    """Get cart count for header display"""
    try:
        cart = request.user.cart
        count = cart.get_total_quantity()
    except Cart.DoesNotExist:
        count = 0
    
    return JsonResponse({'count': count})

# ===== ENHANCED PRODUCT VIEWS =====
# Note: Duplicate product_list function removed to prevent recursion conflicts

def product_detail(request, product_id):
    """Enhanced product detail with related products and reviews"""
    product = get_object_or_404(Product.objects.select_related('category'), id=product_id)
    
    # Get related products
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]
    
    # Get product reviews
    reviews = Comment.objects.filter(product=product).select_related('user')[:5]
    
    # Check if user has liked/favorited this product
    user_liked = False
    user_favorited = False
    if request.user.is_authenticated:
        user_liked = ProductLike.objects.filter(product=product, user=request.user).exists()
        user_favorited = ProductFavorite.objects.filter(product=product, user=request.user).exists()
    
    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'user_liked': user_liked,
        'user_favorited': user_favorited,
        'total_likes': product.likes.count(),
        'total_favorites': product.favorites.count(),
        'total_reviews': product.comments.count()
    }
    
    return render(request, 'shop/product_detail.html', context)

# ===== USER AUTHENTICATION & PROFILE =====

def register(request):
    """Beautiful user registration with profile creation"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create user profile
            UserProfile.objects.create(
                user=user,
                phone_number=form.cleaned_data.get('phone_number', ''),
                city=form.cleaned_data.get('city', ''),
                province=form.cleaned_data.get('province', '')
            )
            
            # Create cart for new user
            Cart.objects.create(user=user)
            
            messages.success(request, 'حساب کاربری شما با موفقیت ایجاد شد!')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'shop/register.html', {'form': form})

@login_required
def profile(request):
    """Enhanced user profile with order history and preferences"""
    user_profile = request.user.profile
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:10]
    favorites = ProductFavorite.objects.filter(user=request.user).select_related('product')[:6]
    
    # Get user statistics
    total_orders = Order.objects.filter(user=request.user).count()
    total_spent = Order.objects.filter(
        user=request.user, 
        status__in=['delivered', 'shipped']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'user_profile': user_profile,
        'orders': orders,
        'favorites': favorites,
        'total_orders': total_orders,
        'total_spent': total_spent
    }
    
    return render(request, 'shop/profile.html', context)

# ===== ORDER MANAGEMENT =====

@login_required
def checkout(request):
    """Beautiful checkout process with multiple payment options"""
    try:
        cart = request.user.cart
        cart_items = cart.items.select_related('product').all()
        
        if not cart_items.exists():
            messages.warning(request, 'سبد خرید شما خالی است!')
            return redirect('cart')
        
        if request.method == 'POST':
            form = CheckoutForm(request.POST)
            if form.is_valid():
                # Create order
                order = Order.objects.create(
                    user=request.user,
                    delivery_method=form.cleaned_data['delivery_method'],
                    shipping_address=form.cleaned_data['shipping_address'],
                    postal_code=form.cleaned_data['postal_code'],
                    phone_number=form.cleaned_data['phone_number'],
                    notes=form.cleaned_data.get('notes', ''),
                    subtotal=cart.get_total_price(),
                    delivery_fee=50000 if cart.get_total_price() < 500000 else 0,
                    total_amount=cart.get_total_price() + (50000 if cart.get_total_price() < 500000 else 0)
                )
                
                # Create order items
                for cart_item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price
                    )
                
                # Clear cart
                cart.items.all().delete()
                
                messages.success(request, f'سفارش شما با موفقیت ثبت شد! شماره سفارش: {order.id}')
                return redirect('order_detail', order_id=order.id)
        else:
            form = CheckoutForm()
        
        context = {
            'cart_items': cart_items,
            'subtotal': cart.get_total_price(),
            'delivery_fee': 50000 if cart.get_total_price() < 500000 else 0,
            'total': cart.get_total_price() + (50000 if cart.get_total_price() < 500000 else 0),
            'form': form
        }
        
        return render(request, 'shop/checkout.html', context)
        
    except Cart.DoesNotExist:
        messages.error(request, 'سبد خرید یافت نشد!')
        return redirect('product_list')

@login_required
def order_detail(request, order_id):
    """Beautiful order detail page with tracking"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.select_related('product').all()
    
    context = {
        'order': order,
        'order_items': order_items
    }
    
    return render(request, 'shop/order_detail.html', context)

@login_required
def order_list(request):
    """User's order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders
    }
    
    return render(request, 'shop/order_list.html', context)

# ===== SOCIAL FEATURES =====

@login_required
def toggle_like(request):
    """Toggle product like with AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            product = get_object_or_404(Product, id=product_id)
            
            like, created = ProductLike.objects.get_or_create(
                product=product,
                user=request.user
            )
            
            if not created:
                like.delete()
                is_liked = False
            else:
                is_liked = True
            
            total_likes = product.likes.count()
            
            return JsonResponse({
                'success': True,
                'is_liked': is_liked,
                'total_likes': total_likes
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'درخواست نامعتبر'})

@login_required
def toggle_favorite(request):
    """Toggle product favorite with AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            product = get_object_or_404(Product, id=product_id)
            
            favorite, created = ProductFavorite.objects.get_or_create(
                product=product,
                user=request.user
            )
            
            if not created:
                favorite.delete()
                is_favorited = False
            else:
                is_favorited = True
            
            total_favorites = product.favorites.count()
            
            return JsonResponse({
                'success': True,
                'is_favorited': is_favorited,
                'total_favorites': total_favorites
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'درخواست نامعتبر'})

# ===== NOTIFICATION SYSTEM =====

@login_required
def notifications(request):
    """User notifications page"""
    notifications = request.user.notifications.all()[:20]
    
    context = {
        'notifications': notifications
    }
    
    return render(request, 'shop/notifications.html', context)

@login_required
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications')

@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications')

def search_products(request):
    """Search products with filters"""
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort_by = request.GET.get('sort', 'name')
    
    products = Product.objects.filter(is_active=True)
    
    # Apply search query
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    # Apply category filter
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Apply price filters
    if min_price:
        products = products.filter(price__gte=float(min_price))
    if max_price:
        products = products.filter(price__lte=float(max_price))
    
    # Apply sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'popular':
        products = products.order_by('-likes_count')
    else:
        products = products.order_by('name')
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    context = {
        'products': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
    }
    
    return render(request, 'shop/search_results.html', context)

def about(request):
    """About page"""
    return render(request, 'shop/about.html')

def contact(request):
    """Contact page"""
    return render(request, 'shop/contact.html')

def ai_assistant_view(request):
    """AI Assistant page view"""
    return render(request, 'shop/ai_assistant.html')
