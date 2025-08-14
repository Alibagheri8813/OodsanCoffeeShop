from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		('shop', '0028_merge_ready_shipping_combined'),
	]

	operations = [
		migrations.AlterField(
			model_name='order',
			name='status',
			field=models.CharField(
				choices=[
					('pending_payment', 'در انتظار پرداخت'),
					('preparing', 'در حال آمــاده‌سازی'),
					('ready_shipping_preparation', 'آماده و در حال آماده‌سازی ارسال'),
					('in_transit', 'بسته در حال رسیدن به مقصد است'),
					('delivered', 'تحویل داده شده'),
					('pickup_ready', 'آماده شده است و لطفاً مراجعه کنید'),
				],
				default='pending_payment',
				max_length=40
			),
		),
	]