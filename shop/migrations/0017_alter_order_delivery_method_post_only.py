from django.db import migrations, models


def set_delivery_method_to_post(apps, schema_editor):
    Order = apps.get_model('shop', 'Order')
    Order.objects.filter(delivery_method__in=['pickup', 'postal']).update(delivery_method='post')


def reverse_set_delivery_method_to_post(apps, schema_editor):
    # Cannot reliably restore previous values; default to 'post'
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0016_cartitem_add_grind_weight_and_unique'),
    ]

    operations = [
        migrations.RunPython(set_delivery_method_to_post, reverse_code=reverse_set_delivery_method_to_post),
        migrations.AlterField(
            model_name='order',
            name='delivery_method',
            field=models.CharField(choices=[('post', 'ارسال پستی')], default='post', max_length=20),
        ),
    ]