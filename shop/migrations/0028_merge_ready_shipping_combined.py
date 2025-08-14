from django.db import migrations


def combine_ready_and_shipping(apps, schema_editor):
	Order = apps.get_model('shop', 'Order')
	Order.objects.filter(status__in=['ready', 'shipping_preparation']).update(status='ready_shipping_preparation')


def reverse_split(apps, schema_editor):
	# Cannot reliably split combined state back; no-op
	pass


class Migration(migrations.Migration):

	dependencies = [
		('shop', '0027_alter_order_status_choices'),
	]

	operations = [
		migrations.RunPython(combine_ready_and_shipping, reverse_split),
	]