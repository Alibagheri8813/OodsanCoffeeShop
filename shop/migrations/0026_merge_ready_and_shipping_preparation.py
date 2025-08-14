from django.db import migrations


def merge_ready_and_shipping_preparation(apps, schema_editor):
	Order = apps.get_model('shop', 'Order')
	Order.objects.filter(status='shipping_preparation').update(status='ready')


def reverse_noop(apps, schema_editor):
	# No safe reverse since original state removed
	pass


class Migration(migrations.Migration):

	dependencies = [
		('shop', '0025_order_intro_margin_applied_amount_and_more'),
	]

	operations = [
		migrations.RunPython(merge_ready_and_shipping_preparation, reverse_noop),
	]