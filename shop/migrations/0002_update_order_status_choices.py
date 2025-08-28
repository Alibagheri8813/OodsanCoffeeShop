# Generated manually for order status update

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0007_video_order_delivery_fee_order_delivery_method_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending_payment', 'در انتظار پرداخت'),
                    ('preparing', 'در حال آمــاده‌سازی'),
                    ('ready', 'آماده شده'),
                    ('shipping_preparation', 'در حال ارسال به اداره پست'),
                    ('in_transit', 'بسته در حال رسیدن به مقصد است'),
                    ('pickup_ready', 'آماده شده است و لطفاً مراجعه کنید'),
                ],
                default='pending_payment',
                max_length=25
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery_method',
            field=models.CharField(
                choices=[
                    ('pickup', 'دریافت حضوری'),
                    ('postal', 'ارسال پستی'),
                ],
                default='pickup',
                max_length=20
            ),
        ),
    ]