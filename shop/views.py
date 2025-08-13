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
from django.db.models import Q, Sum, Count, Avg, F, Min, Max
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from .models import *
from .forms import *
from .error_handling import (
    monitor_performance, safe_transaction, ajax_error_handler, 
    view_error_handler, rate_limit, LoggingContext, optimize_queryset
)
import json
import logging
from django.conf import settings
from decimal import Decimal
from django.contrib.admin.views.decorators import user_passes_test
from django.views.decorators.http import require_http_methods
from django.db.models import F
from django.db import transaction as db_transaction
from random import randint
from django.utils import timezone as dj_timezone

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
        # Get featured products for AI recommendations section
        featured_products = Product.objects.filter(featured=True, stock__gt=0)[:6]
        
        context = {
            'categories': categories,
            'featured_products': featured_products,
        }
        
        return render(request, 'shop/home.html', context)
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

def category_detail(request, category_id=None, slug=None):
    if slug:
        category = get_object_or_404(Category, slug=slug)
    else:
        category = get_object_or_404(Category, id=category_id)
    subcategories = Category.objects.filter(parent=category)
    products = Product.objects.filter(category=category)
    return render(request, 'shop/category_detail.html', {
        'category': category,
        'subcategories': subcategories,
        'products': products,
    })

@monitor_performance
@view_error_handler
def product_detail(request, product_id=None, slug=None):
    """Enhanced product detail with premium features"""
    with LoggingContext('product_detail', request.user, {'product_id': product_id}):
        # Optimize main product query
        if slug:
            product = get_object_or_404(
                Product.objects.select_related('category'),
                slug=slug
            )
        else:
            product = get_object_or_404(
                Product.objects.select_related('category'),
                id=product_id
            )
        
        # Optimize comments query
        comments = optimize_queryset(
            Comment.objects.filter(product=product).order_by('-created_at'),
            select_related=['user']
        )
        
        # Optimize related products query  
        related_products = optimize_queryset(
            Product.objects.filter(category=product.category)
            .exclude(id=product.id)
            .order_by('-featured', '-created_at')[:4],
            select_related=['category']
        )
    
    # Get like count and user like status
    like_count = ProductLike.objects.filter(product=product).count()
    user_liked = False
    if request.user.is_authenticated:
        user_liked = ProductLike.objects.filter(product=product, user=request.user).exists()
    
    # Check if product is in user's favorites
    user_favorites = set()
    user_favorited = False
    if request.user.is_authenticated:
        user_favorites = set(ProductFavorite.objects.filter(
            user=request.user
        ).values_list('product_id', flat=True))
        user_favorited = product.id in user_favorites
    
    # Get user's cart quantity for this product
    cart_quantity = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_quantity = sum(
                item.quantity for item in CartItem.objects.filter(cart=cart, product=product)
            )
        except Cart.DoesNotExist:
            cart_quantity = 0
    
    # Handle POST requests for comments and likes
    if request.method == 'POST':
        if 'text' in request.POST and request.user.is_authenticated:
            text = request.POST.get('text').strip()
            if text:
                Comment.objects.create(
                    product=product,
                    user=request.user,
                    text=text
                )
                messages.success(request, 'نظر شما با موفقیت ثبت شد.')
                return redirect('product_detail', product_id=product_id)
            else:
                messages.error(request, 'نظر نمی‌تواند خالی باشد.')
        
        elif 'like_submit' in request.POST and request.user.is_authenticated:
            like, created = ProductLike.objects.get_or_create(
                product=product,
                user=request.user
            )
            if not created:
                like.delete()
            return redirect('product_detail', product_id=product_id)
    
    # Prepare default weight multipliers if not set
    default_multipliers = {
        '250g': 1.0,
        '500g': 2.0,
        '1kg': 4.0,
        '5kg': 18.0,
        '10kg': 35.0
    }
    
    # Use product-configured options as-is; only fill safe defaults when completely unset (None)
    if product.available_grinds is None:
        product.available_grinds = ['whole_bean', 'coarse', 'medium', 'fine']
    if product.available_weights is None:
        product.available_weights = ['250g', '500g', '1kg']
    if not product.weight_multipliers:
        product.weight_multipliers = {k: v for k, v in default_multipliers.items() if product.available_weights and k in product.available_weights}

    context = {
        'product': product,
        'comments': comments,
        'reviews': comments,  # For template compatibility
        'related_products': related_products,
        'like_count': like_count,
        'total_likes': like_count,
        'total_favorites': product.favorites.count(),
        'total_reviews': comments.count(),
        'user_liked': user_liked,
        'user_favorited': user_favorited,
        'user_favorites': user_favorites,
        'cart_quantity': cart_quantity,
        'available_stock': max(0, product.stock - cart_quantity),
        # New context for enhanced product detail
        'grind_choices': Product.GRIND_TYPE_CHOICES,
        'weight_choices': Product.WEIGHT_CHOICES,
        'available_grinds': product.available_grinds,
        'available_weights': product.available_weights,
        'weight_multipliers': product.weight_multipliers or default_multipliers,
        'base_price': product.price,
    }
    return render(request, 'shop/product_detail.html', context)

# ===== CART: Views and APIs =====

@login_required
def cart_view(request):
    """Display the shopping cart page with totals and delivery fee."""
    try:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart).select_related('product').order_by('-added_at')
        subtotal = sum((item.get_total_price() for item in cart_items), Decimal('0'))
        delivery_fee = Decimal('0')
        if subtotal and subtotal < Decimal('500000'):
            delivery_fee = Decimal('50000')
        total = subtotal + delivery_fee

        has_complete_address = False
        profile = getattr(request.user, 'profile', None)
        if profile:
            has_complete_address = all([
                bool(profile.address),
                bool(profile.city),
                bool(profile.province),
                bool(profile.postal_code),
            ])

        context = {
            'cart_items': list(cart_items),
            'subtotal': subtotal,
            'delivery_fee': delivery_fee,
            'total': total,
            'is_cart_empty': cart_items.count() == 0,
            'has_complete_address': has_complete_address,
        }
        return render(request, 'shop/cart.html', context)
    except Exception as exc:
        logger.error(f"Error rendering cart view: {exc}")
        messages.error(request, 'خطا در نمایش سبد خرید')
        return redirect('product_list')

@login_required
@require_POST
def add_to_cart(request):
    """Add a product to the user's cart.
    Accepts JSON (application/json) or form-encoded (application/x-www-form-urlencoded) bodies.
    """
    try:
        # Safely parse body as JSON when appropriate; otherwise fallback to POST dict
        if request.META.get('CONTENT_TYPE', '').startswith('application/json'):
            try:
                data = json.loads(request.body.decode('utf-8')) if request.body else {}
            except json.JSONDecodeError:
                data = {}
        else:
            data = request.POST

        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        grind_type = data.get('grind_type', 'whole_bean')
        weight = data.get('weight', '250g')

        if not product_id:
            return JsonResponse({'success': False, 'message': 'شناسه محصول ارسال نشده است'}, status=400)

        from .services.cart_service import add_to_cart as svc_add
        response = svc_add(request.user, int(product_id), int(quantity or 1), grind_type, weight)
        status_code = 200 if response.get('success') else 400
        return JsonResponse(response, status=status_code)

    except Exception as exc:
        logger.error(f"add_to_cart error: {exc}")
        return JsonResponse({'success': False, 'message': 'خطا در افزودن به سبد خرید'}, status=500)

@login_required
def update_cart_item(request):
    """Update the quantity of a specific cart item. Accepts JSON POST. GET returns invalid request JSON."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'درخواست نامعتبر'})

    try:
        if request.META.get('CONTENT_TYPE', '').startswith('application/json'):
            try:
                data = json.loads(request.body.decode('utf-8')) if request.body else {}
            except json.JSONDecodeError:
                data = {}
        else:
            data = request.POST

        item_id = data.get('item_id')
        new_quantity = data.get('quantity')

        if item_id is None or new_quantity is None:
            return JsonResponse({'success': False, 'message': 'داده‌های نامعتبر'}, status=400)

        from .services.cart_service import update_cart_item as svc_update
        response = svc_update(request.user, int(item_id), int(new_quantity))
        status_code = 200 if response.get('success') else 400
        return JsonResponse(response, status=status_code)

    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'سبد خرید یافت نشد'}, status=404)
    except Exception as exc:
        logger.error(f"update_cart_item error: {exc}")
        return JsonResponse({'success': False, 'message': 'خطا در به‌روزرسانی سبد خرید'})

@login_required
@require_POST
def remove_from_cart(request):
    """Remove an item from cart and restore product stock."""
    try:
        if request.META.get('CONTENT_TYPE', '').startswith('application/json'):
            try:
                data = json.loads(request.body.decode('utf-8')) if request.body else {}
            except json.JSONDecodeError:
                data = {}
        else:
            data = request.POST

        item_id = data.get('item_id')
        if item_id is None:
            return JsonResponse({'success': False, 'message': 'داده‌های نامعتبر'}, status=400)

        from .services.cart_service import remove_from_cart as svc_remove
        response = svc_remove(request.user, int(item_id))
        status_code = 200 if response.get('success') else 400
        return JsonResponse(response, status=status_code)

    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'سبد خرید یافت نشد'}, status=404)
    except Exception as exc:
        logger.error(f"remove_from_cart error: {exc}")
        return JsonResponse({'success': False, 'message': 'خطا در حذف آیتم از سبد خرید'}, status=500)

@login_required
def cart_count(request):
    """Return total quantity of items in cart."""
    try:
        cart = Cart.objects.get(user=request.user)
        total_count = sum((item.quantity for item in cart.items.all()), 0)
    except Cart.DoesNotExist:
        total_count = 0
    return JsonResponse({'count': total_count})

# ===== AUTH/PROFILE & CHECKOUT (URL compatibility) =====

def register(request):
    """User registration using the enhanced UserRegistrationForm."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create related profile with optional fields
            UserProfile.objects.create(
                user=user,
                phone_number=form.cleaned_data.get('phone_number', ''),
                city=form.cleaned_data.get('city', ''),
                province=form.cleaned_data.get('province', ''),
            )
            messages.success(request, 'ثبت‌نام با موفقیت انجام شد. لطفاً وارد شوید.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'shop/register.html', {'form': form})

@login_required
def profile(request):
    """Compatibility route that forwards to the detailed user profile view."""
    return redirect('user_profile')

@login_required
def checkout(request):
    """Checkout page that creates an order from the user's cart using services."""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('product')

    subtotal = sum((item.get_total_price() for item in cart_items), Decimal('0'))
    delivery_fee = Decimal('0') if subtotal >= Decimal('500000') else Decimal('50000') if subtotal > 0 else Decimal('0')
    total = subtotal + delivery_fee

    # Compute potential intro margin shown on summary (visual only; applied on order create)
    intro_margin_preview = 0
    try:
        p = request.user.profile
        p.ensure_intro_margin_awarded()
        if p.intro_margin_awarded and p.intro_margin_balance and not p.intro_margin_consumed_at:
            intro_margin_preview = int(min(Decimal(str(p.intro_margin_balance)), total))
    except Exception:
        intro_margin_preview = 0

    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            delivery_method = form.cleaned_data['delivery_method']
            address = form.cleaned_data['address']
            postal_code = form.cleaned_data['postal_code']
            notes = form.cleaned_data.get('notes', '')
            from .services.order_service import create_order_from_cart
            result = create_order_from_cart(
                request.user,
                delivery_method=delivery_method,
                address_id=address.id if address else None,
                postal_code=postal_code,
                notes=notes,
            )
            if result.get('success'):
                messages.success(request, 'سفارش شما با موفقیت ثبت شد.')
                return redirect('order_detail', result['order_id'])
            else:
                messages.error(request, result.get('message', 'خطا در ثبت سفارش'))
    else:
        form = CheckoutForm(user=request.user)

    context = {
        'form': form,
        'cart_items': list(cart_items),
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'total': total,
        'user_addresses': list(UserAddress.objects.filter(user=request.user)),
        'intro_margin_preview': intro_margin_preview,
    }
    return render(request, 'shop/checkout.html', context)

@login_required
def change_password(request):
    """Allow the user to change their password using Django's PasswordChangeForm."""
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'رمز عبور شما با موفقیت تغییر یافت.')
            return redirect('user_profile')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'shop/change_password.html', {'form': form})

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
    """Enhanced user profile view with address management"""
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        if created:
            messages.info(request, 'پروفایل شما ایجاد شد. لطفاً اطلاعات خود را تکمیل کنید.')
        
        # Clean up expired unpaid orders before stats
        for o in Order.objects.filter(user=request.user, status='pending_payment'):
            _delete_if_expired_unpaid(o)
        
        # Get or create loyalty program
        loyalty, _ = LoyaltyProgram.objects.get_or_create(user=request.user)
        
        # Get recent orders (last 5)
        recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
        
        # Get user statistics
        total_orders = Order.objects.filter(user=request.user).count()
        total_spent = Order.objects.exclude(status='pending_payment').filter(
            user=request.user
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        favorite_count = ProductFavorite.objects.filter(user=request.user).count()
        
        context = {
            'profile': profile,
            'loyalty': loyalty,
            'recent_orders': recent_orders,
            'total_orders': total_orders,
            'total_spent': total_spent,
            'favorite_count': favorite_count,
        }
        
        return render(request, 'shop/user_profile.html', context)
        
    except Exception as e:
        logger.error(f"Error in user_profile view: {str(e)}")
        messages.error(request, 'خطایی در نمایش پروفایل رخ داد.')
        return redirect('home')

@login_required
def edit_profile(request):
    """Edit user profile information"""
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        if request.method == 'POST':
            form = UserProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
                # Re-check and possibly award intro margin
                try:
                    profile.refresh_from_db()
                    profile.ensure_intro_margin_awarded()
                except Exception:
                    pass
                messages.success(request, 'پروفایل شما با موفقیت به‌روزرسانی شد.')
                return redirect('user_profile')
            else:
                messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
        else:
            form = UserProfileForm(instance=profile)
        
        context = {
            'form': form,
            'profile': profile,
        }
        
        return render(request, 'shop/edit_profile.html', context)
        
    except Exception as e:
        logger.error(f"Error in edit_profile view: {str(e)}")
        messages.error(request, 'خطایی در ویرایش پروفایل رخ داد.')
        return redirect('user_profile')

@login_required
def add_address(request):
    """Add new address for user"""
    try:
        if request.method == 'POST':
            form = UserAddressForm(request.POST)
            if form.is_valid():
                address = form.save(commit=False)
                address.user = request.user
                address.save()
                messages.success(request, 'آدرس جدید با موفقیت اضافه شد.')
                return redirect('user_profile')
            else:
                messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
        else:
            form = UserAddressForm()
        
        context = {
            'form': form,
            'title': 'افزودن آدرس جدید',
        }
        
        return render(request, 'shop/address_form.html', context)
        
    except Exception as e:
        logger.error(f"Error in add_address view: {str(e)}")
        messages.error(request, 'خطایی در افزودن آدرس رخ داد.')
        return redirect('user_profile')

@login_required
def edit_address(request, address_id):
    """Edit existing address"""
    try:
        address = get_object_or_404(UserAddress, id=address_id, user=request.user)
        
        if request.method == 'POST':
            form = UserAddressForm(request.POST, instance=address)
            if form.is_valid():
                form.save()
                messages.success(request, 'آدرس با موفقیت به‌روزرسانی شد.')
                return redirect('user_profile')
            else:
                messages.error(request, 'لطفاً خطاهای فرم را بررسی کنید.')
        else:
            form = UserAddressForm(instance=address)
        
        context = {
            'form': form,
            'address': address,
            'title': 'ویرایش آدرس',
        }
        
        return render(request, 'shop/address_form.html', context)
        
    except Exception as e:
        logger.error(f"Error in edit_address view: {str(e)}")
        messages.error(request, 'خطایی در ویرایش آدرس رخ داد.')
        return redirect('user_profile')

@login_required
def delete_address(request, address_id):
    """Delete user address"""
    try:
        address = get_object_or_404(UserAddress, id=address_id, user=request.user)
        
        # Prevent deletion of default address if it's the only one
        if address.is_default and UserAddress.objects.filter(user=request.user).count() == 1:
            messages.error(request, 'نمی‌توانید تنها آدرس خود را حذف کنید.')
            return redirect('user_profile')
        
        address.delete()
        messages.success(request, 'آدرس با موفقیت حذف شد.')
        
        # If deleted address was default, make another address default
        if address.is_default:
            first_address = UserAddress.objects.filter(user=request.user).first()
            if first_address:
                first_address.is_default = True
                first_address.save()
        
        return redirect('user_profile')
        
    except Exception as e:
        logger.error(f"Error in delete_address view: {str(e)}")
        messages.error(request, 'خطایی در حذف آدرس رخ داد.')
        return redirect('user_profile')

@login_required
def order_history(request):
    # Delete expired unpaid orders before listing
    for o in Order.objects.filter(user=request.user, status='pending_payment'):
        _delete_if_expired_unpaid(o)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/order_history.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    """Beautiful order detail page with tracking"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Auto-delete if expired and unpaid
    if _delete_if_expired_unpaid(order):
        messages.warning(request, 'مهلت پرداخت این سفارش به پایان رسیده و سفارش حذف شد.')
        return redirect('order_history')
    
    order_items = order.items.select_related('product').all()
    
    # Include feedback if exists for template conditional rendering
    feedback = getattr(order, 'feedback', None)
 
    # Provide explicit status lists for template membership checks
    preparing_or_beyond_statuses = ['preparing', 'ready', 'shipping_preparation', 'in_transit', 'pickup_ready']
    ready_or_beyond_statuses = ['ready', 'shipping_preparation', 'in_transit', 'pickup_ready']
    shipping_prep_or_transit_statuses = ['shipping_preparation', 'in_transit']
 
    payment_deadline_ts = None
    if order.status == 'pending_payment':
        deadline = order.created_at + timedelta(minutes=5)
        payment_deadline_ts = int(deadline.timestamp())
    
    context = {
        'order': order,
        'order_items': order_items,
        'feedback': feedback,
        'preparing_or_beyond_statuses': preparing_or_beyond_statuses,
        'ready_or_beyond_statuses': ready_or_beyond_statuses,
        'shipping_prep_or_transit_statuses': shipping_prep_or_transit_statuses,
        'payment_deadline_ts': payment_deadline_ts,
    }
    
    return render(request, 'shop/order_detail.html', context)

@require_http_methods(["POST"])
@login_required
def pay_order(request, order_id):
    """Simulate payment for an order owned by the user and mark it as paid."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Auto-delete if expired and unpaid before attempting payment
    if _delete_if_expired_unpaid(order):
        messages.warning(request, 'مهلت پرداخت این سفارش به پایان رسیده و سفارش حذف شد.')
        return redirect('order_history')
    
    if order.status != 'pending_payment':
        messages.warning(request, 'این سفارش در وضعیت قابل پرداخت نیست.')
        return redirect('order_detail', order_id)
    
    try:
        if order.mark_as_paid(request.user):
            Notification.create_notification(
                user=request.user,
                notification_type='order_status',
                title=f'پرداخت سفارش #{order.id} تایید شد',
                message='پرداخت شما با موفقیت انجام شد و سفارش وارد مرحله آماده‌سازی شد.',
                related_object=order
            )
            messages.success(request, 'پرداخت با موفقیت انجام شد. سفارش شما در حال آماده‌سازی است.')
        else:
            messages.error(request, 'خطا در به‌روزرسانی وضعیت سفارش برای پرداخت.')
    except Exception as e:
        logger.error(f"Error in pay_order: {e}")
        messages.error(request, 'در پردازش پرداخت مشکلی رخ داد.')
    
    return redirect('order_detail', order_id)

@login_required
def order_list(request):
    """User's order history"""
    # Delete expired unpaid orders before listing
    for o in Order.objects.filter(user=request.user, status='pending_payment'):
        _delete_if_expired_unpaid(o)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders
    }
    
    return render(request, 'shop/order_list.html', context)

# ===== SOCIAL FEATURES =====

@rate_limit(requests_per_minute=60)  # Allow more likes per minute
@ajax_error_handler
@safe_transaction
def toggle_like(request):
    """Toggle product like with AJAX"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'برای لایک کردن محصول باید وارد شوید',
            'redirect': '/login/'
        })
    
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

@rate_limit(requests_per_minute=60)  # Allow more favorites per minute  
@ajax_error_handler
@safe_transaction
def toggle_favorite(request):
    """Toggle product favorite with AJAX"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'برای اضافه کردن به علاقه‌مندی‌ها باید وارد شوید',
            'redirect': '/login/'
        })
    
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
    """User notifications page (compatible name)"""
    notifications_list = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/notifications.html', {'notifications': notifications_list})

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark a single notification as read (compatible name)"""
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
    """Mark all notifications as read (compatible name)"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

@login_required
@require_POST
def delete_notification(request, notification_id):
    """Delete a notification (compatible name)"""
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
        has_complete_address = bool(
            profile.address and profile.address.strip() and
            profile.postal_code and profile.postal_code.strip() and
            profile.city and profile.city.strip() and
            profile.province and profile.province.strip()
        )
        return JsonResponse({'has_complete_address': has_complete_address})
    except UserProfile.DoesNotExist:
        return JsonResponse({'has_complete_address': False})

@login_required
@require_POST
def like_product(request, product_id):
    """Like a product (compatible endpoint)"""
    product = get_object_or_404(Product, id=product_id)
    like, created = ProductLike.objects.get_or_create(product=product, user=request.user)
    like_count = ProductLike.objects.filter(product=product).count()
    return JsonResponse({'status': 'liked', 'like_count': like_count})

@login_required
@require_POST
def unlike_product(request, product_id):
    """Unlike a product (compatible endpoint)"""
    product = get_object_or_404(Product, id=product_id)
    try:
        like = ProductLike.objects.get(product=product, user=request.user)
        like.delete()
        like_count = ProductLike.objects.filter(product=product).count()
        return JsonResponse({'status': 'unliked', 'like_count': like_count})
    except ProductLike.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Like not found'}, status=404)

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

# ===== SYSTEM HEALTH & MONITORING =====

@ajax_error_handler
def health_check(request):
    """System health check endpoint"""
    from .error_handling import check_database_health, check_cache_health
    
    # Check database
    db_health = check_database_health()
    
    # Check cache
    cache_health = check_cache_health()
    
    # Overall system status
    overall_healthy = (
        db_health['status'] == 'healthy' and 
        cache_health['status'] == 'healthy'
    )
    
    health_data = {
        'status': 'healthy' if overall_healthy else 'unhealthy',
        'timestamp': timezone.now().isoformat(),
        'components': {
            'database': db_health,
            'cache': cache_health,
        },
        'version': '1.0.0',
        'environment': 'development' if settings.DEBUG else 'production'
    }
    
    status_code = 200 if overall_healthy else 503
    
    return JsonResponse(health_data, status=status_code)

@monitor_performance
@view_error_handler  
def system_status(request):
    """Detailed system status for administrators"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    from django.db import connection
    import sys
    import platform
    
    with LoggingContext('system_status', request.user):
        # Database statistics
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM shop_product")
            product_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM shop_order")
            order_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM auth_user")
            user_count = cursor.fetchone()[0]
        
        # System information
        system_info = {
            'python_version': sys.version,
            'platform': platform.platform(),
            'django_version': '5.1.1',  # Update as needed
        }
        
        # Statistics
        stats = {
            'total_products': product_count,
            'total_orders': order_count, 
            'total_users': user_count,
        }
        
        status_data = {
            'system': system_info,
            'statistics': stats,
            'health': {
                'database': check_database_health(),
                'cache': check_cache_health(),
            },
            'timestamp': timezone.now().isoformat(),
        }
        
        return JsonResponse(status_data)

# ===== PHASE 3: ADVANCED FEATURES VIEWS =====

try:
    from .ai_recommendation_engine import ai_engine
except ImportError:
    ai_engine = None

# AI Recommendations
@login_required
@monitor_performance
def personalized_recommendations(request):
    """Personalized AI recommendations page"""
    try:
        if not ai_engine:
            messages.warning(request, 'سیستم پیشنهادات در حال بروزرسانی است')
            return redirect('shop_home')
            
        # Simple fallback recommendations for now
        featured_products = Product.objects.filter(featured=True, stock__gt=0)[:12]
        trending_products = Product.objects.filter(stock__gt=0).order_by('-created_at')[:6]
        
        context = {
            'recommendations': [{'product': p, 'score': 0.8, 'reason': 'محصول ویژه'} for p in featured_products],
            'trending_products': trending_products,
            'stats': {'total_recommendations': len(featured_products), 'viewed_count': 0, 'view_rate': 0},
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
        return JsonResponse({'status': 'success'})
    except Exception as e:
        logger.error(f"Error tracking recommendation view: {e}")
        return JsonResponse({'status': 'error'})

# Analytics Dashboard
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
        }
        
        # Low Stock Alerts
        low_stock_products = Product.objects.filter(stock__lte=10, stock__gt=0).order_by('stock')
        out_of_stock = Product.objects.filter(stock=0).count()
        
        context = {
            'revenue_data': revenue_data,
            'revenue_growth': 0,  # Simplified for now
            'order_growth': 0,    # Simplified for now
            'top_products': top_products,
            'user_stats': user_stats,
            'low_stock_products': low_stock_products,
            'out_of_stock_count': out_of_stock,
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
        # Simplified customer insights for now
        top_customers = User.objects.annotate(
            total_spent=Sum('orders__total_amount'),
            order_count=Count('orders')
        ).filter(total_spent__gt=0).order_by('-total_spent')[:20]
        
        # Recent activities - simplified
        recent_orders = Order.objects.select_related('user').order_by('-created_at')[:50]
        
        context = {
            'top_customers': top_customers,
            'recent_activities': recent_orders,
            'page_title': 'تحلیل مشتریان'
        }
        
        return render(request, 'shop/customer_insights.html', context)
        
    except Exception as e:
        logger.error(f"Error in customer insights: {e}")
        messages.error(request, 'خطا در بارگیری تحلیل مشتریان')
        return redirect('analytics_dashboard')

# Advanced Search
@monitor_performance
def advanced_search(request):
    """Advanced search with multiple filters"""
    try:
        query = request.GET.get('q', '').strip()
        category_id = request.GET.get('category')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        availability = request.GET.get('availability')
        sort_by = request.GET.get('sort', 'relevance')
        
        # Start with all active products
        products = Product.objects.filter(stock__gte=0)
        
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
        
        # Apply sorting
        if sort_by == 'price_low':
            products = products.order_by('price')
        elif sort_by == 'price_high':
            products = products.order_by('-price')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        else:  # relevance
            products = products.order_by('-featured', '-created_at')
        
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

# Enhanced Product Detail
@monitor_performance
def enhanced_product_detail(request, product_id):
    """Enhanced product detail page with AI recommendations"""
    try:
        product = get_object_or_404(Product, id=product_id, stock__gte=0)
        
        # Get similar products (simple category-based for now)
        similar_products = Product.objects.filter(
            category=product.category,
            stock__gt=0
        ).exclude(id=product_id)[:6]
        
        # Get product reviews
        reviews = Comment.objects.filter(
            product=product, 
            is_approved=True
        ).select_related('user').order_by('-created_at')
        
        # Calculate average rating
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        
        context = {
            'product': product,
            'similar_products': similar_products,
            'reviews': reviews,
            'avg_rating': avg_rating,
            'page_title': product.name
        }
        
        return render(request, 'shop/enhanced_product_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error in enhanced product detail: {e}")
        messages.error(request, 'خطا در بارگیری محصول')
        return redirect('shop_home')

# Loyalty Program
@login_required
@monitor_performance
def loyalty_dashboard(request):
    """Loyalty program dashboard"""
    try:
        # Simplified loyalty program for now
        user_orders = Order.objects.filter(
            user=request.user,
            status__in=['paid', 'processing', 'shipped', 'delivered']
        )
        
        total_spent = user_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        order_count = user_orders.count()
        
        # Simple tier calculation
        if total_spent >= 5000000:
            tier = 'platinum'
            tier_display = 'پلاتینیوم'
        elif total_spent >= 2000000:
            tier = 'gold'
            tier_display = 'طلایی'
        elif total_spent >= 500000:
            tier = 'silver'
            tier_display = 'نقره‌ای'
        else:
            tier = 'bronze'
            tier_display = 'برنزی'
        
        points = int(total_spent / 1000)  # 1 point per 1000 toman
        
        context = {
            'loyalty': {
                'tier': tier,
                'tier_display': tier_display,
                'points': points,
                'total_earned_points': points,
                'total_redeemed_points': 0
            },
            'total_spent': total_spent,
            'order_count': order_count,
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
        messages.success(request, 'قابلیت رد کردن امتیاز به زودی فعال خواهد شد!')
        return JsonResponse({'status': 'success', 'message': 'به زودی...'})
    except Exception as e:
        logger.error(f"Error redeeming points: {e}")
        return JsonResponse({'status': 'error', 'message': 'خطا در رد کردن امتیاز'})

# API Endpoints
@login_required
@ajax_error_handler
def api_recommendations(request):
    """API endpoint for recommendations"""
    try:
        # Simple fallback recommendations
        products = Product.objects.filter(featured=True, stock__gt=0)[:6]
        
        recommendations = []
        for product in products:
            recommendations.append({
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'image': product.image.url if product.image else None,
                'score': 0.8,
                'reason': 'محصول ویژه'
            })
        
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
        # Simple user analytics
        user_orders = Order.objects.filter(user=request.user)
        total_spent = user_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        data = {
            'recent_activities': [],
            'segment': {
                'type': 'مشتری عادی',
                'total_spent': float(total_spent),
                'order_count': user_orders.count()
            },
            'loyalty': {
                'tier': 'برنزی',
                'points': int(total_spent / 1000),
                'total_earned': int(total_spent / 1000)
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        logger.error(f"Error in API analytics: {e}")
        return JsonResponse({'error': 'خطا در بارگیری تحلیلات'}, status=500)

@require_http_methods(["POST"])
@login_required
def transition_order_status(request, order_id):
    """API endpoint for transitioning order status (staff-only)"""
    try:
        order = get_object_or_404(Order, id=order_id)
 
        # Staff-only transitions
        if not request.user.is_staff:
            return JsonResponse({'error': 'عدم دسترسی'}, status=403)
 
        data = json.loads(request.body)
        new_status = data.get('status')
 
        if not new_status:
            return JsonResponse({'error': 'وضعیت جدید مشخص نشده است'}, status=400)
 
        # Validate status choice
        valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return JsonResponse({'error': 'وضعیت نامعتبر'}, status=400)
 
        # Attempt transition
        if order.transition_to(new_status, request.user):
            return JsonResponse({
                'success': True,
                'status': order.status,
                'status_display': order.get_status_display(),
                'status_color': order.get_status_badge_color(),
                'message': f'وضعیت سفارش به "{order.get_status_display()}" تغییر کرد'
            })
        else:
            return JsonResponse({'error': 'امکان تغییر وضعیت وجود ندارد'}, status=400)
             
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error transitioning order status: {e}")
        return JsonResponse({'error': 'خطا در تغییر وضعیت سفارش'}, status=500)

@require_http_methods(["POST"])
@login_required
@user_passes_test(lambda u: u.is_staff)
def mark_order_as_paid(request, order_id):
    """API endpoint for marking order as paid (staff only)"""
    try:
        order = get_object_or_404(Order, id=order_id)
        
        if order.mark_as_paid(request.user):
            return JsonResponse({
                'success': True,
                'status': order.status,
                'status_display': order.get_status_display(),
                'status_color': order.get_status_badge_color(),
                'message': 'سفارش پرداخت شده و در حال آماده‌سازی قرار گرفت'
            })
        else:
            return JsonResponse({'error': 'امکان تغییر وضعیت وجود ندارد'}, status=400)
            
    except Exception as e:
        logger.error(f"Error marking order as paid: {e}")
        return JsonResponse({'error': 'خطا در علامت‌گذاری سفارش'}, status=500)

@require_http_methods(["POST"])
@login_required
@user_passes_test(lambda u: u.is_staff)
def mark_order_as_ready(request, order_id):
    """API endpoint for marking order as ready (staff only)"""
    try:
        order = get_object_or_404(Order, id=order_id)
        
        if order.mark_as_ready(request.user):
            return JsonResponse({
                'success': True,
                'status': order.status,
                'status_display': order.get_status_display(),
                'status_color': order.get_status_badge_color(),
                'message': 'سفارش آماده شد'
            })
        else:
            return JsonResponse({'error': 'امکان تغییر وضعیت وجود ندارد'}, status=400)
            
    except Exception as e:
        logger.error(f"Error marking order as ready: {e}")
        return JsonResponse({'error': 'خطا در علامت‌گذاری سفارش'}, status=500)

@require_http_methods(["POST"])
@login_required
@user_passes_test(lambda u: u.is_staff)
def start_order_shipping_preparation(request, order_id):
    """API endpoint for starting shipping preparation (staff only)"""
    try:
        order = get_object_or_404(Order, id=order_id)
        
        if order.start_shipping_preparation(request.user):
            return JsonResponse({
                'success': True,
                'status': order.status,
                'status_display': order.get_status_display(),
                'status_color': order.get_status_badge_color(),
                'message': 'سفارش وارد مرحله آماده‌سازی ارسال شد'
            })
        else:
            return JsonResponse({'error': 'امکان تغییر وضعیت وجود ندارد یا سفارش پستی نیست'}, status=400)
            
    except Exception as e:
        logger.error(f"Error starting shipping preparation: {e}")
        return JsonResponse({'error': 'خطا در آماده‌سازی ارسال'}, status=500)

@require_http_methods(["POST"])
@login_required
@user_passes_test(lambda u: u.is_staff)
def mark_order_in_transit(request, order_id):
    """API endpoint for marking order as in transit (staff only)"""
    try:
        order = get_object_or_404(Order, id=order_id)
        
        if order.mark_in_transit(request.user):
            return JsonResponse({
                'success': True,
                'status': order.status,
                'status_display': order.get_status_display(),
                'status_color': order.get_status_badge_color(),
                'message': 'سفارش در حال ارسال قرار گرفت'
            })
        else:
            return JsonResponse({'error': 'امکان تغییر وضعیت وجود ندارد'}, status=400)
            
    except Exception as e:
        logger.error(f"Error marking order in transit: {e}")
        return JsonResponse({'error': 'خطا در علامت‌گذاری سفارش'}, status=500)

@require_http_methods(["GET"])
@login_required
def get_order_status(request, order_id):
    """API endpoint to get current order status"""
    try:
        order = get_object_or_404(Order, id=order_id)
        
        # Check permissions
        if not request.user.is_staff and order.user != request.user:
            return JsonResponse({'error': 'عدم دسترسی'}, status=403)
        
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'status': order.status,
            'status_display': order.get_status_display(),
            'status_color': order.get_status_badge_color(),
            'delivery_method': order.delivery_method,
            'delivery_method_display': order.get_delivery_method_display(),
            'can_transition_to': {
                status: label for status, label in Order.STATUS_CHOICES 
                if order.can_transition_to(status)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting order status: {e}")
        return JsonResponse({'error': 'خطا در دریافت وضعیت سفارش'}, status=500)

def voice_ai_assistant_page(request):
    """Voice AI Assistant page"""
    context = {
        'page_title': 'Voice Coffee Expert',
        'page_description': 'Your Professional Coffee Industry Expert'
    }
    return render(request, 'shop/voice_ai_assistant.html', context)

@require_POST
@login_required
def toggle_product_like(request, product_id):
    """Toggle like status for a specific product via AJAX"""
    try:
        product = get_object_or_404(Product, id=product_id)
        
        like, created = ProductLike.objects.get_or_create(
            product=product,
            user=request.user
        )
        
        if not created:
            # Unlike the product
            like.delete()
            is_liked = False
            message = 'پسند برداشته شد'
        else:
            # Like the product
            is_liked = True
            message = 'محصول پسندیده شد'
            
        total_likes = ProductLike.objects.filter(product=product).count()
        
        return JsonResponse({
            'success': True,
            'is_liked': is_liked,
            'total_likes': total_likes,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Error toggling product like: {e}")
        return JsonResponse({
            'success': False,
            'message': 'خطا در پردازش درخواست'
        }, status=500)

@require_POST
@login_required
def toggle_product_favorite(request, product_id):
    """Toggle favorite status for a specific product via AJAX"""
    try:
        product = get_object_or_404(Product, id=product_id)
        
        favorite, created = ProductFavorite.objects.get_or_create(
            product=product,
            user=request.user
        )
        
        if not created:
            # Remove from favorites
            favorite.delete()
            is_favorited = False
            message = 'از علاقه‌مندی‌ها حذف شد'
        else:
            # Add to favorites
            is_favorited = True
            message = 'به علاقه‌مندی‌ها اضافه شد'
            
        total_favorites = ProductFavorite.objects.filter(product=product).count()
        
        return JsonResponse({
            'success': True,
            'is_favorited': is_favorited,
            'total_favorites': total_favorites,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Error toggling product favorite: {e}")
        return JsonResponse({
            'success': False,
            'message': 'خطا در پردازش درخواست'
        }, status=500)

@require_http_methods(["POST"])
@login_required
@ajax_error_handler
def add_product_comment(request, product_id):
    """Add a comment to a product via AJAX"""
    try:
        # Get product
        product = get_object_or_404(Product, id=product_id)
        
        # Parse JSON data
        data = json.loads(request.body)
        comment_text = data.get('text', '').strip()
        
        if not comment_text:
            return JsonResponse({
                'success': False,
                'message': 'نظر نمی‌تواند خالی باشد.'
            })
        
        # Create comment
        comment = Comment.objects.create(
            product=product,
            user=request.user,
            text=comment_text
        )
        
        # Format the date for display
        from django.utils import timezone
        import jdatetime
        
        # Convert to Jalali date
        jalali_date = jdatetime.datetime.fromgregorian(datetime=comment.created_at)
        formatted_date = jalali_date.strftime('%d %B %Y - %H:%M')
        
        # Return success response with comment data
        return JsonResponse({
            'success': True,
            'message': 'نظر شما با موفقیت ثبت شد.',
            'comment': {
                'user': comment.user.username,
                'text': comment.text,
                'date': formatted_date
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'داده‌های ارسالی نامعتبر است.'
        })
    except Exception as e:
        logger.error(f"Error adding product comment: {e}")
        return JsonResponse({
            'success': False,
            'message': 'خطا در ثبت نظر'
        }, status=500)

@login_required
@require_POST
def submit_order_feedback(request, order_id):
    """Submit feedback for an order once it's ready for pickup (as delivered status does not exist)."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Only allow feedback when order is effectively completed for user
    if order.status != 'pickup_ready':
        return JsonResponse({'success': False, 'message': 'در این مرحله امکان ارسال بازخورد وجود ندارد'})
    
    # Prevent duplicate feedback
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
    feedback = OrderFeedback.objects.create(
        order=order,
        rating=rating,
        comment=comment
    )
    
    # Notify admins about new feedback (optional)
    for admin_user in User.objects.filter(is_staff=True):
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

# Helper to restore stock when deleting an unpaid order
def _restore_stock_for_order(order: Order):
    with db_transaction.atomic():
        for item in order.items.select_related('product').all():
            Product.objects.filter(id=item.product_id).update(stock=F('stock') + item.quantity)

def _delete_if_expired_unpaid(order: Order) -> bool:
    if order.status == 'pending_payment':
        deadline = order.created_at + timedelta(minutes=5)
        if timezone.now() > deadline:
            _restore_stock_for_order(order)
            order.delete()
            return True
    return False

@login_required
@require_http_methods(["POST"])
def send_phone_verification_code(request):
    """Send OTP SMS to user's phone (Iran). Accept a posted phone number and persist it before sending."""
    try:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        # Read phone number from request (form or JSON)
        try:
            data = request.POST or json.loads(request.body.decode('utf-8') or '{}')
        except Exception:
            data = {}
        posted_phone = (data.get('phone_number') or data.get('phone') or '').strip()

        # If a phone number is provided, persist it and reset verification
        if posted_phone:
            normalized_phone = posted_phone
            if normalized_phone != (profile.phone_number or '').strip():
                profile.phone_number = normalized_phone
                profile.is_phone_verified = False
                profile.save(update_fields=['phone_number', 'is_phone_verified'])

        phone = (profile.phone_number or '').strip()
        if not phone:
            return JsonResponse({'success': False, 'message': 'ابتدا شماره تلفن خود را در پروفایل ثبت کنید.'}, status=400)

        if profile.is_phone_verified:
            return JsonResponse({'success': True, 'message': 'شماره شما قبلاً تایید شده است.'})

        code = f"{randint(100000, 999999)}"
        profile.phone_verify_code = code
        profile.phone_verify_expires_at = dj_timezone.now() + timedelta(minutes=5)
        profile.save(update_fields=['phone_verify_code', 'phone_verify_expires_at'])

        # SMS sending (mock or provider integration)
        from .sms_provider import send_sms
        try:
            send_sms(phone, f"کد تایید شما: {code}")
        except Exception as e:
            logger.error(f"SMS send failed: {e}")

        return JsonResponse({'success': True, 'message': 'کد تایید ارسال شد.'})
    except Exception as e:
        logger.error(f"send_phone_verification_code error: {e}")
        return JsonResponse({'success': False, 'message': 'خطا در ارسال کد تایید'}, status=500)

@login_required
@require_http_methods(["POST"])
def verify_phone_code(request):
    """Verify submitted OTP code."""
    try:
        data = request.POST or json.loads(request.body.decode('utf-8') or '{}')
        code = (data.get('code') or '').strip()
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if not code:
            return JsonResponse({'success': False, 'message': 'کد تایید را وارد کنید.'}, status=400)
        if not profile.phone_verify_code or not profile.phone_verify_expires_at:
            return JsonResponse({'success': False, 'message': 'ابتدا کد تایید را دریافت کنید.'}, status=400)
        if dj_timezone.now() > profile.phone_verify_expires_at:
            return JsonResponse({'success': False, 'message': 'مهلت کد تایید به پایان رسیده است.'}, status=400)
        if code != profile.phone_verify_code:
            return JsonResponse({'success': False, 'message': 'کد تایید نادرست است.'}, status=400)

        profile.is_phone_verified = True
        profile.phone_verify_code = ''
        profile.phone_verify_expires_at = None
        profile.save(update_fields=['is_phone_verified', 'phone_verify_code', 'phone_verify_expires_at'])

        # Check award after successful verification
        try:
            profile.ensure_intro_margin_awarded()
        except Exception:
            pass

        return JsonResponse({'success': True, 'message': 'شماره تلفن با موفقیت تایید شد.'})
    except Exception as e:
        logger.error(f"verify_phone_code error: {e}")
        return JsonResponse({'success': False, 'message': 'خطا در تایید کد'}, status=500)
