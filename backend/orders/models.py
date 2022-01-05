import twitter_profiles
from django.db import models
from django.db.models import signals
from django.dispatch import receiver  
from twitter_profiles.models import TwitterProfile
from util_functions.get_twitter_images import get_user_id
from django.core.exceptions import ObjectDoesNotExist
from urllib.parse import urlparse
import requests
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
import os 
from django.conf import settings
MEDIA_ROOT_DIRECTORY = settings.MEDIA_ROOT 

def max_file_size(value):
    limit = 10 * 1024 * 1024
    if value.size > limit:
        raise ValidationError('File too large. Size should not exceed 10 MiB.')

def get_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT /<last_name>/<filename>
    folder_name = instance.last_name + '-' + instance.twitter_handle
    return 'orders/{0}/{1}'.format(folder_name, filename)

class Order(models.Model):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    twitter_handle = models.CharField(max_length=100)
    source_image_url = models.URLField(blank=True)
    source_image = models.ImageField(upload_to=get_directory_path, null=True, blank=True, default='', validators=[max_file_size])
    ordered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=PENDING
    )

    def add_source_image_using_url(self):
        if self.source_image_url and not self.source_image:
            print("Adding 'source image' using a URL value")
            img_url = self.source_image_url
            name = urlparse(img_url).path.split('/')[-1]
            response = requests.get(img_url)

            if response.status_code == 200:
                self.source_image.save(name, ContentFile(response.content), save=True)
        else: 
            print("no source image URL value setl or source_image is already set")

    def set_in_progress(self):
        self.status = Order.IN_PROGRESS
        self.save()

    def get_output_filename(self):

        FILENAME_SUFFIX = '-twitter-collage'
        FILENAME_EXTENSION = '.jpg'

        finalOutputName = self.twitter_handle + '-' + str(self.id) + FILENAME_SUFFIX + FILENAME_EXTENSION

        collagesDirectory = os.path.join(MEDIA_ROOT_DIRECTORY, 'collages') 
        outputPath = os.path.join(collagesDirectory, finalOutputName)
    
        return outputPath


    def __str__(self):
        obj_name = self.email + '-' + self.twitter_handle
        return obj_name

@receiver(signals.post_save, sender=Order)
def start_order_processing(sender, instance, created, **kwargs):
    '''
    When a new collage order is created, this checks for whether a TwitterProfile exists for the handle. 
    '''
    if created:

        print('Hit start_order_processing')
        instance.add_source_image_using_url()

        requestedTwitterHandle = instance.twitter_handle

        if (requestedTwitterHandle):
            try:
                existingProfile = TwitterProfile.objects.get(twitter_handle=requestedTwitterHandle)
                print("Existing twitter profile found")
                existingProfile.get_latest_images()
            except TwitterProfile.DoesNotExist: 
                print("New twitter profile requested, creating....")

                userID = get_user_id(requestedTwitterHandle)

                if userID != 0:
                    newTwitterProfile = TwitterProfile(
                        twitter_handle=requestedTwitterHandle,
                        images_count=0,
                        latest_tweet_id=0,
                        user_id=userID
                    )

                    newTwitterProfile.save()
                    newTwitterProfile.get_latest_images()
                else:
                    print("Twitter user not found!!")
        else:
            print("Object was created with no twitter handle, nothing to see here...")