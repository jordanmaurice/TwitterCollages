# mosaic_utils.py
import os
import random
import argparse
from PIL import Image, ImageDraw, ImageFilter, ImageFile, UnidentifiedImageError
import numpy as np
import math
import colorsys
import time
import requests
from io import BytesIO
import cv2
from sklearn.cluster import KMeans
from collections import Counter
import json
import random
from functools import lru_cache
from django.conf import settings
from twitter_images.models import TwitterImage
from django.core.files import File
ImageFile.LOAD_TRUNCATED_IMAGES = True
from django.core.files.storage import default_storage
import io

MEDIA_ROOT_DIRECTORY = settings.MEDIA_ROOT 

'''
Given a twitter profile, retrieve the source images
'''
def get_twitter_source_images(twitterProfile):
    imageData = []

    # Get all source images from that twitter profile
    twitterSourceImages = TwitterImage.objects.filter(twitter_profile=twitterProfile)

    for sourceImage in twitterSourceImages:
        print("Processing image from Tweet: {}".format(sourceImage.tweet_id))
        
        filePath = sourceImage.image.file
        
        try:
            image = default_storage.open(sourceImage.image.name, 'rb')
            print("image type is: {}".format(type(image)))
            file_data = image.read()
            image.close()

            print("file_data is: {}".format(type(file_data)))
            
            pilImage = Image.open(sourceImage.image, 'r', None)

            if (is_valid_image(pilImage)):
                print(filePath)
                inputImage = {}
                inputImage['filepath'] = filePath
                inputImage['dominant_color'] = sourceImage.get_dominant_color()
                inputImage['average_color'] = sourceImage.get_average_color()
                imageData.append(inputImage)
                pilImage.load()
                
        except ValueError:
            print("value was not as expected")
        except TypeError:
            print("type was not as expected...") 
        except UnidentifiedImageError:
            print("image not identified")
        except Exception:
            print("Some kinda exception....")

    print("New images added: {}".format(len(imageData)))

    # Exit early if no valid input images are returned
    if not imageData:
        print('No input images found. Exiting.')
        exit()
    else:
        print("Found {} valid images to use in the mosaic".format(len(imageData)))

    return imageData

def is_valid_image(image):
    """
    Parameters:
    image - A PIL image object

    Return value:
    Boolean - True if the image has three channels to it
    """

    im = np.array(image)
    
    try:
        w, h, d = im.shape
    except:
        return False

    return True

def get_average_rbg(image):
    """
    Parameters:
    image - a PIL image object

    Return value:
    rgbColor - a tuple representation of the average RGB color of the given image
    """
    im = np.array(image)
    w, h, d = im.shape

    tupleAverage = tuple(np.average(im.reshape(w * h, d), axis=0))

    # Convert to a list, then round the averages to decimal points
    listColor = list(tupleAverage)

    for i in range(len(listColor)):
        listColor[i] = round(listColor[i], 0)

    rgbColor = tuple(listColor)

    return rgbColor

def get_dominant_color(imagePath, k=4):
    """
    Parameters:
    imagePath - A path to the image we're working on
    k = Number of clusters to use

    dominant color is found by running k means on the
    pixels & returning the centroid of the largest cluster

    Return value:
    dominantColor - A tuple value of the dominant color, ex:  (56.2423442, 34.0834233, 70.1234123)
    """

    # Read in image of interest
    bgrImage = cv2.imread(imagePath)

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

    return tuple(dominantColor)

def get_grid_size(targetImage):
    """
    Parameters:
    targetImage: (PIL Image) - The image we're rebuilding into a mosaic
    """

    MAX_GRID_SIZE_LENGTH = 300

    targetImageWidth, targetImageHeight = targetImage.size

    widthRatio = targetImageWidth / targetImageHeight
    heightRatio = targetImageHeight / targetImageWidth

    if widthRatio < 1:
        gridWidth = MAX_GRID_SIZE_LENGTH * widthRatio
        gridHeight = MAX_GRID_SIZE_LENGTH
    else:
        gridHeight = MAX_GRID_SIZE_LENGTH * heightRatio
        gridWidth = MAX_GRID_SIZE_LENGTH

    roundedGridValues = (int(round(gridHeight, 0)), int(round(gridWidth, 0)))

    print("Grid size: {}".format(roundedGridValues))

    return roundedGridValues

def get_best_match_colors(pieceColorAverage, inputImages):
    """
    Parameters:
    pieceColorAverage - The average RGB value of the piece of the mosaic to be created
    inputImages - A list of dictionaries containing the image inputs
    Return Type: Integer - An index value for which of the inputImages to use.
    """

    print("Finding best match for color: {}".format(pieceColorAverage))

    NUMBER_OF_IMAGES_TO_RETURN = 12

    distanceValues = [float("inf") for x in range(NUMBER_OF_IMAGES_TO_RETURN)]

    distanceIndeces = []

    for index, inputColorAverage in enumerate(inputImages):
        colorDistance = get_color_distance(pieceColorAverage, inputColorAverage)

        if colorDistance < max(distanceValues):
            # Pop the largest from the list
            distanceValues.pop(distanceValues.index(max(distanceValues)))
            distanceValues.append(colorDistance)

            distanceIndeces.append((index, colorDistance))

    filterResult = [tup for tup in distanceIndeces if any(i in tup for i in distanceValues)]

    tupleResult = tuple(filterResult)
    print(tupleResult)
    return tupleResult


def get_color_distance(pieceColorAverage, inputColorAverage):
    distance = ((inputColorAverage[0] - pieceColorAverage[0]) * (inputColorAverage[0] - pieceColorAverage[0]) +
                (inputColorAverage[1] - pieceColorAverage[1]) * (inputColorAverage[1] - pieceColorAverage[1]) +
                (inputColorAverage[2] - pieceColorAverage[2]) * (inputColorAverage[2] - pieceColorAverage[2]))

    return distance


def get_composite_image(sourceImage, color):
    array = np.zeros([sourceImage.size[0], sourceImage.size[1], 3], dtype=np.uint8)
    array[:, :sourceImage.size[1]] = [color[0], color[1], color[2]]

    colorImage = Image.fromarray(array)

    mask = Image.new("L", sourceImage.size, 128)

    return Image.composite(sourceImage, colorImage, mask)


def get_target_image(imageURL):
    response = requests.get(imageURL)
    imageContent = BytesIO(response.content)
    
    try:
        targetImage = Image.open(imageContent)
    except:
        targetImage = False

    if not targetImage:
        print("Error opening target image. Check URL or something.")
        quit()
    else:
        return targetImage


def split_image(image, gridSize):
    """
    Parameters:
    image - An Image instance of the target image that is being used to create a mosaic
    gridSize - A tuple of ints (width, height) that match the size of the grid pieces to be made

    Return Type:
    A List of Image instances of the cropped pieces of the source image
    """

    croppedImagePieces = []

    originalImageWidth, originalImageHeight = image.size
    print("Target image size: {}".format(image.size))
    
    gridWidth, gridHeight = gridSize

    print("Grid size: {}".format(gridSize))
    
    gridPieceWidth, gridPieceHeight = int(originalImageWidth / gridHeight), int(
        originalImageHeight / gridWidth)
    
    print("Cropped mosaic piece size: {}x{}".format(gridPieceWidth, gridPieceHeight))

    # Loop through the grid size creating cropped chunks of the original image.  Add them to the cropped pieces list
    for j in range(gridWidth):
        for i in range(gridHeight):
            left = i * gridPieceWidth
            top = j * gridPieceHeight
            right = (i + 1) * gridPieceWidth
            bottom = (j + 1) * gridPieceHeight
            
            croppedImagePiece = image.crop((left, top, right, bottom))

            croppedImagePieces.append(croppedImagePiece)

    return croppedImagePieces


def resize_images(inputImagesFolder, keepAspectRatio):
    """
    Parameters:
    inputImages - A list of Image instances from getImages function
    keepAspectRatio - A boolean to determine how to resize image (crop to exact size, or keep aspect ratio of the original image)

    Returns Type: - A list of Image instances in the correct size for the grid
    """

    resizedImages = []

    print('Resizing images...')

    dimensions = (50, 50)

    print(f"Max tile dimensions: {dimensions}")

    for img in inputImagesFolder:
        if keepAspectRatio:
            img.thumbnail(dimensions)
            resizedImages.append(img)
        else:
            resizedImage = img.resize(dimensions)
            resizedImages.append(resizedImage)

    return resizedImages