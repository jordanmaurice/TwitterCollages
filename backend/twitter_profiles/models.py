from django.db import models
from util_functions.get_twitter_images import add_twitter_images, add_twitter_images_v2

class TwitterProfile(models.Model):
    twitter_handle = models.CharField(max_length=100, unique=True, verbose_name="Twitter Handle")
    user_id = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Fetched At")
    latest_tweet_id = models.BigIntegerField(verbose_name="Latest Tweet ID read", help_text="This was the most recent tweet ID requested.")
    images_count = models.PositiveIntegerField(default=0, verbose_name="Images Count")

    def __str__(self):
        return self.twitter_handle

    def get_latest_images(self):
        success_message = add_twitter_images_v2(self)
        print(success_message)