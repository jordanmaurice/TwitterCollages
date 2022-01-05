# Generated by Django 4.0 on 2022-01-04 05:36

from django.db import migrations, models
import orders.models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_order_ordered_at_order_source_image_url_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='source_image',
            field=models.ImageField(blank=True, null=True, upload_to=orders.models.get_directory_path),
        ),
    ]
