# Generated by Django 4.0 on 2022-01-04 00:58

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TwitterProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('twitter_handle', models.CharField(max_length=100, unique=True, verbose_name='Twitter Handle')),
                ('user_id', models.BigIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Last Fetched At')),
                ('latest_tweet_id', models.BigIntegerField(help_text='This was the most recent tweet ID requested.', verbose_name='Latest Tweet ID read')),
                ('images_count', models.PositiveIntegerField(default=0, verbose_name='Images Count')),
            ],
        ),
    ]
