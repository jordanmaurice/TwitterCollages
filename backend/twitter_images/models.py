from django.db import models
import cv2
from sklearn.cluster import KMeans
from collections import Counter
import json
import numpy as np
from PIL import Image

def get_upload_folder_name(instance, filename):
    # Saves photos as /media/twitter_source_images/<twitter_handle>/<filename>
    return 'twitter_images/{0}/{1}'.format(instance.twitter_profile.twitter_handle, filename)
         
class TwitterImage(models.Model):
    twitter_profile = models.ForeignKey("twitter_profiles.TwitterProfile", on_delete=models.CASCADE)
    tweet_id = models.BigIntegerField()
    image = models.ImageField(upload_to=get_upload_folder_name)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    dominant_color = models.JSONField(null=True)
    average_color = models.JSONField(null=True)

    def __str__(self):
        return self.twitter_profile.twitter_handle + '-' + str(self.tweet_id)

    def set_dominant_color(self):
        if self.image:
            print('Called get dominant color')
            k=4
            """
            Parameters:
            k = Number of clusters to use

            dominant color is found by running k means on the
            pixels & returning the centroid of the largest cluster

            Return value:
            dominantColor - A tuple value of the dominant color, ex:  (56.2423442, 34.0834233, 70.1234123)
            """

            # Read in image of interest
            bgrImage = cv2.imread(self.image.path)

            # Convert to HSV
            hsvImage = cv2.cvtColor(bgrImage, cv2.COLOR_BGR2HSV)

            # Reshape the image to be a list of pixels
            hsvImage = hsvImage.reshape((hsvImage.shape[0] * hsvImage.shape[1], 3))

            # Cluster and assign labels to the pixels 
            clt = KMeans(n_clusters=k)
            labels = clt.fit_predict(hsvImage)

            # Count labels to find most popular
            labelCounts = Counter(labels)

            # Subset out most popular centroid
            dominantColor = clt.cluster_centers_[labelCounts.most_common(1)[0][0]]

            dominantColorTuple = tuple(dominantColor)

            print("Dom color is: ".format(dominantColorTuple))

            self.dominant_color = dominantColorTuple
     
            jsonString = {"dominant_color": dominantColorTuple}
            self.dominant_color = jsonString
            self.save()
        else:
            print("Image value not set")

    def get_dominant_color(self):
        if self.image and self.dominant_color:
            print(type(self.dominant_color['dominant_color']))
            return self.dominant_color['dominant_color']

            # data = json.loads(self.dominant_color)
            # print("Dominant color is: {}".format(data['dominant_color']))
            # return data['dominant_color']
        else: 
            return False

    def set_average_color(self):
        """
        Return value:
        rgbColor - a tuple representation of the average RGB color of the given image
        """
        image = Image.open(self.image)

        im = np.array(image)
        w, h, d = im.shape

        tupleAverage = tuple(np.average(im.reshape(w * h, d), axis=0))

        # Convert to a list, then round the averages to decimal points
        listColor = list(tupleAverage)

        for i in range(len(listColor)):
            listColor[i] = round(listColor[i], 0)

        rgbColor = tuple(listColor)

        print(rgbColor)
        jsonString = {"average_color": rgbColor}
        self.average_color = jsonString
        self.save()
    
    def get_average_color(self):
        if self.image and self.average_color:
            print(type(self.average_color['average_color']))
            return self.average_color['average_color']
        else: 
            return False