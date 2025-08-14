from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		('shop', '0026_merge_ready_and_shipping_preparation'),
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
					('in_transit', 'بسته در حال رسیدن به مقصد است'),
					('delivered', 'تحویل داده شده'),
					('pickup_ready', 'آماده شده است و لطفاً مراجعه کنید'),
				],
				default='pending_payment',
				max_length=25
			),
		),
	]