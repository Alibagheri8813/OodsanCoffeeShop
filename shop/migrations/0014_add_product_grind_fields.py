# Generated manually to fix missing fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0013_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='available_grinds',
            field=models.JSONField(blank=True, default=list, help_text='Available grind types'),
        ),
        migrations.AddField(
            model_name='product',
            name='available_weights',
            field=models.JSONField(blank=True, default=list, help_text='Available weight options'),
        ),
        migrations.AddField(
            model_name='product',
            name='weight_multipliers',
            field=models.JSONField(blank=True, default=dict, help_text='Price multipliers for different weights'),
        ),
    ]