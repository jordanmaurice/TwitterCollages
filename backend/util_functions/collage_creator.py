from PIL import Image, ImageDraw, ImageFilter
import time
import random
import os
from orders.models import Order
from twitter_profiles.models import TwitterProfile

from util_functions.mosaic_utils import \
    get_average_rbg, get_best_match_colors, get_twitter_source_images, get_composite_image, get_target_image, split_image, get_grid_size

def create_image_grid(mosaicPieceImageList, dimensions):
    # Unpack the grid_width and height from the dimensions tuple
    gridWidth, gridHeight = dimensions 

    # Set width and height variables to the largest size of the output images 
    width = max([img.size[0] for img in mosaicPieceImageList])
    height = max([img.size[1] for img in mosaicPieceImageList])

    print("Max image width: {}".format(width))
    print("Max image height: {}".format(height))

    mosaicFinalWidth = gridHeight * width
    mosaicFinalHeight = gridWidth * height

    mosaicFinalSize = (mosaicFinalWidth, mosaicFinalHeight)
    print("Final Mosaic Size: {}".format(mosaicFinalSize))

    # Create a new PIL Image object
    # https://pillow.readthedocs.io/en/stable/reference/Image.html#constructing-images

    gridImage = Image.new('RGB', mosaicFinalSize)

    # Loop through the all the mosaic pieces inserting them into the new gridImage object 
    for index in range(len(mosaicPieceImageList)):
        row = int(index / gridHeight)
        col = index - gridHeight * row
        pieceCoordinate = (col * width, row * height) 

        # https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.paste
        gridImage.paste(mosaicPieceImageList[index], pieceCoordinate)

    return gridImage


def get_tuple_input_images(inputImages):
    averageColors = []

    for image in inputImages:
        averageColor = image['average_color']
        averageColors.append(averageColor)

    tupleAverageColors = tuple(averageColors)

    return tupleAverageColors


def create_photo_mosaic(targetImage, targetImagePath, inputImages, gridSize, inputImageDirectory=None, reuseImages=True):

    """
    Loop through each of the cropped pieces of the target image and try to find the best, then add that
    input image that most closely matches the cropped piece
    """

    print("Grid size is: {}".format(gridSize))
    outputImages = []

    count = 0

    calculatedColors = {}

    skippedCount = 0

    tupleImageAverages = get_tuple_input_images(inputImages)

    targetImagePieces = split_image(targetImage, gridSize)

    batch_size = int(len(targetImagePieces) / 10)

    print("Beginning color matching, this may take a while.  Updates will be added every 10% progression...")

    for count, img in enumerate(targetImagePieces):
        # Calculate the average color fo the current grid piece
        pieceColorAverage = get_average_rbg(img)

        # If the color has not previously been calculated, then calculate the closest ones
        if pieceColorAverage not in calculatedColors:
            matchingColors = get_best_match_colors(pieceColorAverage, tupleImageAverages)
            calculatedColors[pieceColorAverage] = matchingColors
        else:
            # Otherwise use the existing colors
            matchingColors = calculatedColors[pieceColorAverage]
            skippedCount += 1

        # Choose a random close color image to use
        matchIndex = random.choice(matchingColors)[0]

        # Get the filepath and open the image
        bestMatchFilepath = inputImages[matchIndex]['filepath']
        bestMatchImage = Image.open(bestMatchFilepath)

        # Create a new image with the average color of the piece overlayed on top
        compositeImage = get_composite_image(bestMatchImage, pieceColorAverage)

        # Add the image to the outputImages list
        outputImages.append(compositeImage)

        # Print progress every 10%
        if count > 0 and batch_size > 10 and count % batch_size == 0:
            print('Processed %d of %d...' % (count, len(targetImagePieces)))

    print("Skipped: {} images".format(skippedCount))
    

    return create_image_grid(outputImages, gridSize)





'''
Give this an order object in order to proceed
'''
def create_collage_v2(order):
    # Start timer for how long this whole process takes
    startTime = time.time()

    # Set the order to in progress status 
    order.set_in_progress()

    targetImage = get_target_image(order.source_image_url)

    twitterUsername = order.twitter_handle

    print('Reading input images from db...')
    twitterProfile = TwitterProfile.objects.get(twitter_handle=twitterUsername)

    inputImages = get_twitter_source_images(twitterProfile)

    gotImagesTime = time.time()

    print("Time taken to gather all input images: {}".format(str(gotImagesTime-startTime)))

    gridSize = get_grid_size(targetImage)

    outputFilename = order.get_output_filename()

    # Allow the mosaic to re-use photos from the input.
    reuseImages = True

    print('Starting photomosaic creation...')

    # Create photomosaic
    mosaicImage = create_photo_mosaic(targetImage, order.source_image_url, inputImages, gridSize)

    # Write photomosaic to file
    FILE_FORMAT = "jpeg"
    mosaicImage.save(outputFilename, FILE_FORMAT)

    print("Saved output to: {}".format(outputFilename))

    print('Completed. ')
    endTime = time.time()
    print("Time taken: {}".format(str(endTime - startTime)))
    
    return outputFilename