from decimal import Decimal
from typing import Dict, Tuple
from django.db import transaction
from django.shortcuts import get_object_or_404

from shop.models import Cart, CartItem, Product


def _calculate_cart_totals(cart: Cart) -> Tuple[int, int]:
    """Return (cart_total_int, cart_count) for the given cart."""
    cart_items_qs = cart.items.select_related('product')
    cart_total = sum((item.get_total_price() for item in cart_items_qs), Decimal('0'))
    cart_count = sum((item.quantity for item in cart_items_qs), 0)
    return int(cart_total), cart_count


@transaction.atomic
def add_to_cart(user, product_id: int, quantity: int = 1, grind_type: str = 'whole_bean', weight: str = '250g') -> Dict:
    """Add product to the user's cart with inventory reservation.

    Decreases product stock when quantity increases; restores when item removed elsewhere.
    Returns a dict suitable for JSON responses.
    """
    if quantity is None:
        quantity = 1
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        quantity = 1

    if quantity == 0:
        # No-op keeps system stable; report success gracefully
        cart, _ = Cart.objects.get_or_create(user=user)
        total, count = _calculate_cart_totals(cart)
        return {"success": True, "cart_total": total, "cart_count": count}

    if quantity < 0:
        return {"success": False, "message": "تعداد نامعتبر است"}

    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        grind_type=grind_type or 'whole_bean',
        weight=weight or '250g',
        defaults={'quantity': 0}
    )

    new_quantity = cart_item.quantity + quantity
    if new_quantity < 0:
        new_quantity = 0

    delta = new_quantity - cart_item.quantity
    if delta > 0:
        if product.stock < delta:
            return {
                'success': False,
                'message': 'موجودی کافی نیست',
                'available_stock': product.stock
            }
        product.stock -= delta
        product.save(update_fields=['stock'])

    if new_quantity == 0 and cart_item.id:
        cart_item.delete()
    else:
        cart_item.quantity = new_quantity
        cart_item.save(update_fields=['quantity'])

    total, count = _calculate_cart_totals(cart)
    return {"success": True, "cart_total": total, "cart_count": count}


@transaction.atomic
def update_cart_item(user, item_id: int, new_quantity: int) -> Dict:
    """Set a cart item's quantity, adjusting stock accordingly."""
    cart = Cart.objects.get(user=user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    product = cart_item.product

    try:
        new_quantity = int(new_quantity)
    except (TypeError, ValueError):
        return {"success": False, "message": "تعداد نامعتبر است"}

    if new_quantity < 0:
        return {"success": False, "message": "تعداد نامعتبر است"}

    if new_quantity == 0:
        product.stock += cart_item.quantity
        product.save(update_fields=['stock'])
        cart_item.delete()
        item_total_int = 0
    else:
        delta = new_quantity - cart_item.quantity
        if delta > 0:
            if product.stock < delta:
                return {
                    'success': False,
                    'message': 'موجودی کافی نیست',
                    'available_stock': product.stock
                }
            product.stock -= delta
            product.save(update_fields=['stock'])
        elif delta < 0:
            product.stock += (-delta)
            product.save(update_fields=['stock'])

        cart_item.quantity = new_quantity
        cart_item.save(update_fields=['quantity'])
        # Compute updated item total after save
        try:
            item_total_int = int(cart_item.get_total_price())
        except Exception:
            item_total_int = 0

    total, count = _calculate_cart_totals(cart)
    return {"success": True, "cart_total": total, "cart_count": count, "item_total": item_total_int}


@transaction.atomic
def remove_from_cart(user, item_id: int) -> Dict:
    """Remove a cart item and restore its stock."""
    cart = Cart.objects.get(user=user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

    product = cart_item.product
    product.stock += cart_item.quantity
    product.save(update_fields=['stock'])

    cart_item.delete()

    total, count = _calculate_cart_totals(cart)
    return {"success": True, "message": 'آیتم با موفقیت حذف شد', "cart_total": total, "cart_count": count}