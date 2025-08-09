from django.db import migrations, models
import django.db.models.deletion
import django.utils.text


def populate_category_slugs(apps, schema_editor):
    Category = apps.get_model('shop', 'Category')
    for category in Category.objects.all():
        if not getattr(category, 'slug', None):
            base = django.utils.text.slugify(category.name, allow_unicode=True)
            candidate = base or 'category'
            i = 1
            Model = Category.__class__
            while Category.objects.filter(slug=candidate).exclude(pk=category.pk).exists():
                i += 1
                candidate = f"{base}-{i}" if base else f"category-{i}"
            category.slug = candidate
            category.save(update_fields=['slug'])


def populate_product_slugs(apps, schema_editor):
    Product = apps.get_model('shop', 'Product')
    for product in Product.objects.all():
        if not getattr(product, 'slug', None):
            base = django.utils.text.slugify(product.name, allow_unicode=True)
            candidate = base or 'product'
            i = 1
            while Product.objects.filter(slug=candidate).exclude(pk=product.pk).exists():
                i += 1
                candidate = f"{base}-{i}" if base else f"product-{i}"
            product.slug = candidate
            product.save(update_fields=['slug'])


class Migration(migrations.Migration):
    dependencies = [
        ('shop', '0017_alter_order_delivery_method_post_only'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='slug',
            field=models.SlugField(blank=True, db_index=True, max_length=160, unique=True),
        ),
        migrations.AddField(
            model_name='product',
            name='slug',
            field=models.SlugField(blank=True, db_index=True, max_length=220, unique=True),
        ),
        migrations.RunPython(populate_category_slugs, migrations.RunPython.noop),
        migrations.RunPython(populate_product_slugs, migrations.RunPython.noop),
    ]