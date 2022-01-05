# Generated by Django 4.0 on 2022-01-01 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_alter_order_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('PE', 'Pending'), ('IP', 'In Progress'), ('CO', 'Completed'), ('CA', 'Cancelled')], default='PE', max_length=2),
        ),
    ]