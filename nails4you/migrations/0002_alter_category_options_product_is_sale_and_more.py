# Generated by Django 5.1.2 on 2024-11-05 23:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nails4you', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name_plural': 'categories'},
        ),
        migrations.AddField(
            model_name='product',
            name='is_sale',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='product',
            name='sale_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=7),
        ),
    ]
