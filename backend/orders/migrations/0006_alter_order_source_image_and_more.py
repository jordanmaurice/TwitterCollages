# Generated by Django 4.0 on 2022-01-04 06:44

from django.db import migrations, models
import orders.models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_order_source_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='source_image',
            field=models.ImageField(blank=True, default='', null=True, upload_to=orders.models.get_directory_path),
        ),
        migrations.AlterField(
            model_name='order',
            name='source_image_url',
            field=models.URLField(blank=True),
        ),
    ]
