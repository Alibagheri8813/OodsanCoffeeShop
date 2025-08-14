from decimal import Decimal
from typing import Dict
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.db import models

from shop.models import Cart, CartItem, Order, OrderItem, Notification, UserAddress, Product


def _delivery_fee_for_subtotal(subtotal: Decimal) -> Decimal:
    return Decimal('50000') if subtotal > 0 else Decimal('0')


@transaction.atomic
def create_order_from_cart(user, delivery_method: str, address_id: int, postal_code: str, notes: str = '') -> Dict:
    """Create an order from the user's cart.

    - Validates address and stock
    - Computes subtotal and delivery fee
    - Applies one-time intro margin if eligible
    - Creates Order and OrderItems with current unit prices
    - Decrements product stock
    - Clears the cart
    - Sends notifications
    """
    cart, _ = Cart.objects.get_or_create(user=user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('product').select_for_update()

    if not cart_items.exists():
        return {"success": False, "message": "سبد خرید شما خالی است"}

    # Require a valid address owned by user
    try:
        address = get_object_or_404(UserAddress, id=address_id, user=user)
        shipping_address = f"{address.title} - {address.full_address} - {address.city} - {address.state}"
    except Exception:
        return {"success": False, "message": "لطفاً یک آدرس معتبر انتخاب کنید"}

    # Validate stock availability
    for item in cart_items:
        if item.product.stock < item.quantity:
            return {"success": False, "message": f"موجودی محصول '{item.product.name}' کافی نیست"}

    subtotal = sum((item.get_total_price() for item in cart_items), Decimal('0'))
    delivery_fee = _delivery_fee_for_subtotal(subtotal)
    total_before_margin = subtotal + delivery_fee

    # Calculate intro margin discount if eligible
    intro_margin_to_apply = Decimal('0')
    try:
        profile = user.profile
        # Ensure award if the profile just became complete
        profile.ensure_intro_margin_awarded()
        if profile.intro_margin_awarded and profile.intro_margin_balance and not profile.intro_margin_consumed_at:
            intro_margin_to_apply = min(Decimal(str(profile.intro_margin_balance)), total_before_margin)
    except Exception:
        intro_margin_to_apply = Decimal('0')

    total = total_before_margin - intro_margin_to_apply

    order = Order.objects.create(
        user=user,
        status='pending_payment',
        delivery_method=delivery_method or 'post',
        delivery_fee=delivery_fee,
        subtotal=subtotal,
        total_amount=total,
        shipping_address=shipping_address,
        postal_code=postal_code or '',
        phone_number=getattr(getattr(user, 'profile', None), 'phone_number', ''),
        notes=notes or '',
        intro_margin_applied_amount=int(intro_margin_to_apply) if intro_margin_to_apply else 0,
    )

    items_payload = []
    for item in cart_items:
        unit_price = item.get_unit_price()
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=unit_price,
            grind_type=item.grind_type,
            weight=item.weight,
        )
        # decrement stock
        Product.objects.filter(id=item.product_id).update(stock=models.F('stock') - item.quantity)
        items_payload.append({
            'product': item.product.name,
            'qty': item.quantity,
            'price': int(unit_price)
        })

    # Clear cart
    cart_items.delete()

    # If we applied margin, mark it as consumed on profile
    if intro_margin_to_apply > 0:
        try:
            profile.intro_margin_balance = Decimal('0')
            from django.utils import timezone
            profile.intro_margin_consumed_at = timezone.now()
            profile.save(update_fields=['intro_margin_balance', 'intro_margin_consumed_at'])
        except Exception:
            pass

    # Notify user and admins
    base_message_total = int(total_before_margin)
    final_message_total = int(total)
    margin_note = f" با {int(intro_margin_to_apply)} تومان اعتبار خوش‌آمدگویی" if intro_margin_to_apply > 0 else ''

    Notification.create_notification(
        user=user,
        notification_type='order_new',
        title=f'سفارش جدید ثبت شد (#{order.id})',
        message=f'سفارش شما با مبلغ {final_message_total} تومان{margin_note} ثبت شد.'
    )
    Notification.create_admin_notification(
        notification_type='order_new',
        title=f'سفارش جدید #{order.id}',
        message=f'کاربر {user.username} سفارشی به مبلغ {final_message_total} ثبت کرد. (قبل از اعتبار: {base_message_total})'
    )

    return {"success": True, "order_id": order.id, "total": int(total)}