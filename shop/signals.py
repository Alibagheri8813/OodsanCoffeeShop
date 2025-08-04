from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models import Q

from .models import Order, Notification, LoyaltyProgram

@receiver(pre_save, sender=Order)
def store_old_status(sender, instance, **kwargs):
    """Keep track of the order status before it gets saved so we can detect
    changes in the post_save handler without an additional DB query."""
    if instance.pk:
        try:
            prev = Order.objects.get(pk=instance.pk)
            instance._old_status = prev.status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        # New order – nothing to compare against
        instance._old_status = None


@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    """Create real-time notifications for admins and users whenever an order is
    created or its status changes."""
    status_names = dict(Order.STATUS_CHOICES)

    if created:
        # Notify admins – broadcast one record for each staff user so badge
        # counters remain user-specific.
        staff_users = User.objects.filter(is_staff=True, is_active=True)
        for admin in staff_users:
            Notification.create_notification(
                user=admin,
                notification_type='order_new',
                title=f'سفارش جدید #{instance.id}',
                message=f'سفارش جدید توسط {instance.user.username} ثبت شد.',
                related_object=instance,
            )

        # Notify the customer as well
        Notification.create_notification(
            user=instance.user,
            notification_type='order_new',
            title='ثبت سفارش',
            message=f'سفارش شما با شماره #{instance.id} با موفقیت ثبت شد.',
            related_object=instance,
        )
    else:
        old_status = getattr(instance, '_old_status', None)
        if old_status and old_status != instance.status:
            # Customer notification
            Notification.create_notification(
                user=instance.user,
                notification_type='order_status',
                title='به‌روزرسانی وضعیت سفارش',
                message=f'وضعیت سفارش #{instance.id} به "{status_names.get(instance.status, instance.status)}" تغییر یافت.',
                related_object=instance,
            )

            # Admin notification for every staff
            staff_users = User.objects.filter(is_staff=True, is_active=True)
            for admin in staff_users:
                Notification.create_notification(
                    user=admin,
                    notification_type='order_status',
                    title=f'تغییر وضعیت سفارش #{instance.id}',
                    message=f'سفارش #{instance.id} اکنون "{status_names.get(instance.status, instance.status)}" است.',
                    related_object=instance,
                )

    # === Automatic workflow transitions ===
    # 1. After payment success → move to 'preparing' if necessary
    if instance.status in ['paid']:
        # Avoid recursion: only update if not already converted
        instance.status = 'preparing'
        instance.save(update_fields=['status'])
        return  # Further signals will handle notification

    # 2. Ready → auto pickup_ready for pickup orders
    if instance.status == 'ready' and instance.delivery_method == 'pickup':
        instance.status = 'pickup_ready'
        instance.save(update_fields=['status'])