from django.db import models

def get_upload_folder_name(instance, filename):
    # file will be uploaded to MEDIA_ROOT /<last_name>-<twitter_handle>/collages/<filename>
    folder_name = instance.order.last_name + '-' + instance.order.twitter_handle
    return 'orders/{0}/collages/{1}'.format(folder_name, filename)
         
class Collage(models.Model):
    twitter_profile = models.ForeignKey("twitter_profiles.TwitterProfile", on_delete=models.CASCADE)
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE)
    collage_image = models.ImageField(upload_to=get_upload_folder_name)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated At")