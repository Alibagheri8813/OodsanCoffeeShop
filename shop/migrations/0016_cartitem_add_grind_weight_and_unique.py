from django.db import migrations, models


def merge_cartitem_duplicates(apps, schema_editor):
    CartItem = apps.get_model('shop', 'CartItem')
    from django.db.models import Count, Sum

    # After adding new fields with defaults, duplicates may exist where
    # (cart, product, grind_type, weight) are identical. Merge them.
    duplicates = (
        CartItem.objects.values('cart_id', 'product_id', 'grind_type', 'weight')
        .annotate(num=Count('id'), total_qty=Sum('quantity'))
        .filter(num__gt=1)
    )

    for dup in duplicates:
        items = list(
            CartItem.objects.filter(
                cart_id=dup['cart_id'],
                product_id=dup['product_id'],
                grind_type=dup['grind_type'],
                weight=dup['weight'],
            ).order_by('id')
        )
        if not items:
            continue
        keeper = items[0]
        keeper.quantity = dup['total_qty'] or keeper.quantity
        keeper.save(update_fields=['quantity'])
        # Delete the rest
        for extra in items[1:]:
            extra.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0015_add_order_item_grind_weight_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='grind_type',
            field=models.CharField(choices=[('whole_bean', 'اسیاب نشده'), ('coarse', 'ترک'), ('medium_coarse', 'موکاپات'), ('medium', 'اسپرسو ساز نیمه صنعتی'), ('medium_fine', 'اسپرسوساز صنعتی'), ('fine', 'اسپرسوساز خانگی')], default='whole_bean', max_length=20),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='weight',
            field=models.CharField(choices=[('250g', '250 گرم'), ('500g', '500 گرم'), ('1kg', '1 کیلوگرم'), ('5kg', '5 کیلوگرم'), ('10kg', '10 کیلوگرم')], default='250g', max_length=10),
        ),
        migrations.RunPython(merge_cartitem_duplicates, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name='cartitem',
            unique_together={('cart', 'product', 'grind_type', 'weight')},
        ),
    ]