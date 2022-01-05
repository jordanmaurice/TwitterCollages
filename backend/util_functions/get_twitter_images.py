import tweepy
from tweepy import OAuthHandler
import json
import wget
import os
from PIL import Image
import requests
from io import StringIO
from io import BytesIO
import uuid
import logging
import threading
import time
from django.conf import settings
from urllib.parse import urlparse
import requests
from django.core.files.base import ContentFile
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile
from django.core.files import File
from functools import partial
import multiprocessing
import django
from twitter_images.models import TwitterImage
from django.db import models

'''
Twitter API access keys and info
'''
CONSUMER_KEY = 'meWjWd1QmiPrMqt2Wt2wuxNQD'
CONSUMER_SECRET = 'iNV8TohCejkEwOZB7qjPdcgy3lNEuCOD4tON644yqMLA7B475q'
ACCESS_TOKEN = '1385839520164192257-OF3KqSYvy2qxXyVssUSPCaGh7vZ7am'
ACCESS_TOKEN_SECRET = 'zGpt9BYrnbE2trH34ocFrIPwrtL4lZdBK9iSCQwXlLOLY'

ROOT_DIRECTORY = settings.MEDIA_ROOT 

def get_all_tweets_from_user(twitterProfile):
    print("Fetching tweets from Twitter handle: {}".format(twitterProfile.twitter_handle))

    latestID = twitterProfile.latest_tweet_id

    print("Latest ID to fetch from: {}".format(latestID))

    if latestID != 0:       
        # Get the tweets of a user, including retweets, disclude replies..
        tweets = api.user_timeline(screen_name=twitterProfile.twitter_handle,
            count=200,
            include_rts=True,
            exclude_replies=True,
            max_id=latestID-1
        )
    else:
        tweets = api.user_timeline(screen_name=twitterProfile.twitter_handle,
            count=200,
            include_rts=True,
            exclude_replies=True
        )

    last_id = tweets[-1].id
    
    while (True):
        more_tweets = api.user_timeline(
            screen_name=twitterProfile.twitter_handle,
            count=200,
            include_rts=True,
            exclude_replies=True,
            max_id=last_id-1
        )

        # There are no more tweets
        if (len(more_tweets) == 0):
            break
        else:
            print("Fetching next 200...")
            last_id = more_tweets[-1].id-1
            tweets = tweets + more_tweets

    return tweets

'''
Given a twitter handle, returns the ID string from Twitter of the given username
'''
def get_user_id(twitter_handle):
    try:
        user = api.get_user(screen_name=twitter_handle)
        user_id = user.id_str
        print("The ID of the user is : " + user_id)
        return user_id

    except:
        print("User was not found!")
        return 0

def tweet_has_media(tweet):
    media = tweet.entities.get('media', [])
    return (len(media) > 0)

def get_only_tweets_with_media(tweets):
    tweetsWithMediaAttachments = [x for x in tweets if tweet_has_media(x)]
    return tweetsWithMediaAttachments
    

def get_media_meta(tweet):
    '''
    Given a tweet object, return a dictionary of the Tweet ID, and the Image Thumbnail URL
    '''

    media = tweet.entities.get('media', [])
    imageURL = media[0]['media_url']+'?name=thumb'

    return {
        'id': tweet.id,
        'imageURL': imageURL
    }

def get_media_info(mediaTweets):
    mediaList = []

    for tweet in mediaTweets:
        tweetMeta = get_media_meta(tweet)
        mediaList.append(tweetMeta)
    
    return mediaList


'''
Parameters: 
mediaItem: Dictionary containing two keys, the tweetID registered under 'id', and the thumbnail URL registered under 'imageURL'
twitterProfile: instance of the TwitterProfile django class
existingTweetIDs: list of twitter IDs that were already parsed
'''
def create_image_source(mediaItem, twitterProfile, existingTweetIDs):
    tweetID = mediaItem['id']
    imageURL = mediaItem['imageURL']

    if(tweetID not in existingTweetIDs):
        response = requests.get(imageURL)
        
        try:
            print("Downloaded image from URL: {}".format(imageURL))
            img = Image.open(BytesIO(response.content))
            dimensions = (50,50)
            thumbImage = img.resize(dimensions)
        except:
            print("Error downloading image from {}".format(imageURL))
            thumbImage = False
            pass    
        
        if thumbImage:
            twitterImageObject = TwitterImage(tweet_id=tweetID, twitter_profile=twitterProfile)
            twitterImageObject.save()
            
            # Generate a unique filename
            img_name = str(uuid.uuid4())+".jpg"

            # Create a BytesIO() object
            blob = BytesIO()

            # Convert the image to RGB if needed
            if thumbImage.mode != 'RGB':
                thumbImage = thumbImage.convert('RGB')

            thumbImage.save(blob, 'JPEG')

            twitterImageObject.image.save(img_name,File(blob))

            return twitterImageObject

        else:
            # If something went wrong with saving the object, delete the twitterImage
            print('something went wrong with saving the object, delete the twitterImage')

def create_image_source_v2(twitterProfile, existingTweetIDs, mediaItem):
    tweetID = mediaItem['id']
    imageURL = mediaItem['imageURL']

    if(tweetID not in existingTweetIDs):
        response = requests.get(imageURL)
        
        try:
            print("Downloaded image from URL: {}".format(imageURL))
            img = Image.open(BytesIO(response.content))
            dimensions = (50,50)
            thumbImage = img.resize(dimensions)
        except:
            print("Error downloading image from {}".format(imageURL))
            thumbImage = False
            pass    
        
        if thumbImage:
            twitterImageObject = TwitterImage(tweet_id=tweetID, twitter_profile=twitterProfile)
            twitterImageObject.save()
            
            # Generate a unique filename
            img_name = str(uuid.uuid4())+".jpg"

            # Create a BytesIO() object
            blob = BytesIO()

            # Convert the image to RGB if needed
            if thumbImage.mode != 'RGB':
                thumbImage = thumbImage.convert('RGB')

            thumbImage.save(blob, 'JPEG')

            twitterImageObject.image.save(img_name,File(blob))

            return twitterImageObject

        else:
            # If something went wrong with saving the object, delete the twitterImage
            print('something went wrong with saving the object, delete the twitterImage')

def get_existing_tweet_ids(twitterProfile):
    # Query for the images from a given twitter profile
    existingImages = TwitterImage.objects.filter(twitter_profile=twitterProfile)

    if (existingImages):
        tweetIDs = []
        for twitterImage in existingImages:
            tweetIDs.append(twitterImage.tweet_id)
        return tweetIDs
    else:
        return []

def add_twitter_images_v2(twitterProfile):   
    # Get the tweets from the User
    tweetsFromUser = get_all_tweets_from_user(twitterProfile)

    # Reduce the list of tweets to only tweets with media attachments
    onlyMediaAttachedTweets = get_only_tweets_with_media(tweetsFromUser)

    # Get a list of dictionaries that contain the id, imageURL
    mediaList = get_media_info(onlyMediaAttachedTweets)
    
    existingTweets = get_existing_tweet_ids(twitterProfile)

    print("Found {} tweets in total".format(len(tweetsFromUser)))
    print("Found {} tweets with media".format(len(onlyMediaAttachedTweets)))


    pool = multiprocessing.Pool()
    func = partial(create_image_source_v2, twitterProfile, existingTweets)
    pool.map(func, mediaList)
    pool.close()
    pool.join()

def add_twitter_images(twitterProfile):
    # Get the tweets from the User
    tweetsFromUser = get_all_tweets_from_user(twitterProfile)

    # Reduce the list of tweets to only tweets with media attachments
    onlyMediaAttachedTweets = get_only_tweets_with_media(tweetsFromUser)

    # Get a list of dictionaries that contain the id, imageURL
    mediaList = get_media_info(onlyMediaAttachedTweets)
    
    existingTweets = get_existing_tweet_ids(twitterProfile)

    print("Found {} tweets in total".format(len(tweetsFromUser)))
    print("Found {} tweets with media".format(len(onlyMediaAttachedTweets)))

    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    threads = list()

    for mediaItem in mediaList:
        logging.info("Main: create and start thread %s.", mediaItem['id'])
        x = threading.Thread(target=create_image_source, args=(mediaItem, twitterProfile, existingTweets))
        threads.append(x)
        x.start()

    return "Much Success"








@classmethod
def parse(cls, api, raw):
    status = cls.first_parse(api, raw)
    setattr(status, 'json', json.dumps(raw))
    return status
    
# Status() is the data model for a tweet
tweepy.models.Status.first_parse = tweepy.models.Status.parse
tweepy.models.Status.parse = parse

# User() is the data model for a user profile
tweepy.models.User.first_parse = tweepy.models.User.parse
tweepy.models.User.parse = parse

# You need to do it for all the models you need

auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

api = tweepy.API(auth)