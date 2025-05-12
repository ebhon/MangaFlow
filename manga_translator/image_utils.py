# Import required libraries for image processing
import os
import cv2
import numpy as np
from PIL import Image, ImageFile

# Enable loading of truncated images to handle corrupted files
ImageFile.LOAD_TRUNCATED_IMAGES = True

def reload_and_save_images(folder_path):
    """
    Reloads and resaves all images in a folder to ensure they are properly formatted.
    This function helps prevent issues with corrupted or improperly formatted images.
    
    Args:
        folder_path (str): Path to the folder containing images to process
    """
    # Process each image file in the specified folder
    for filename in os.listdir(folder_path):
        # Only process image files with common extensions
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            path = os.path.join(folder_path, filename)
            try:
                # Open image and convert to RGB format
                img = Image.open(path)
                img = img.convert("RGB")
                # Save the processed image back to the same location
                img.save(path)
            except Exception as e:
                print(f"Skipping {filename}: {e}")

def preprocess_image(image_path):
    """
    Preprocesses an image for better text detection and OCR.
    Applies grayscale conversion, blur, and adaptive thresholding.
    
    Args:
        image_path (str): Path to the image file to preprocess
        
    Returns:
        numpy.ndarray: Preprocessed image ready for text detection
    """
    # Read image in grayscale mode
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    # Apply median blur to reduce noise
    image = cv2.medianBlur(image, 3)
    # Apply adaptive thresholding to enhance text regions
    image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return image

def enhance_text_region(image_region):
    """
    Enhance text clarity in an image region before OCR.
    Applies multiple image processing techniques to improve text readability.
    
    Args:
        image_region (numpy.ndarray): The image region containing text
        
    Returns:
        numpy.ndarray: Enhanced image region with improved text clarity
    """
    # Convert to grayscale if the image is in color
    gray = cv2.cvtColor(image_region, cv2.COLOR_BGR2GRAY) if len(image_region.shape) == 3 else image_region
    # Apply adaptive thresholding to create binary image
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    # Apply denoising to remove noise
    denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to enhance contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    return enhanced 