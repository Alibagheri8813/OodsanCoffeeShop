# Generated manually to add grind_type and weight fields to OrderItem

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0014_add_product_grind_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='grind_type',
            field=models.CharField(
                choices=[
                    ('whole_bean', 'اسیاب نشده'),
                    ('coarse', 'ترک'),
                    ('medium_coarse', 'موکاپات'),
                    ('medium', 'اسپرسو ساز نیمه صنعتی'),
                    ('medium_fine', 'اسپرسوساز صنعتی'),
                    ('fine', 'اسپرسوساز خانگی'),
                ],
                default='whole_bean',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='weight',
            field=models.CharField(
                choices=[
                    ('250g', '250 گرم'),
                    ('500g', '500 گرم'),
                    ('1kg', '1 کیلوگرم'),
                    ('5kg', '5 کیلوگرم'),
                    ('10kg', '10 کیلوگرم'),
                ],
                default='250g',
                max_length=10
            ),
        ),
    ]