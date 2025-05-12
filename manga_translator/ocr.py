# Import required libraries for OCR and image processing
import re
import cv2
import numpy as np
from manga_ocr import MangaOcr

def validate_ocr_result(text, image_region):
    """
    Validate OCR results to filter out hallucinations or low-confidence detections.
    This function performs multiple checks to ensure the OCR result is reliable:
    1. Text length check
    2. Image sharpness check using Laplacian variance
    3. Contrast check
    4. Text density check
    
    Args:
        text (str): The OCR result text to validate
        image_region (numpy.ndarray): The image region that was processed
        
    Returns:
        bool: True if the OCR result is valid, False otherwise
    """
    # Check if text is too short or empty
    if not text or len(text.strip()) < 2:
        return False
    
    # Convert to grayscale if needed
    gray = cv2.cvtColor(image_region, cv2.COLOR_BGR2GRAY) if len(image_region.shape) == 3 else image_region
    
    # Check image sharpness using Laplacian variance
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian_var < 50:  # Low variance indicates blurry image
        return False
    
    # Check image contrast
    min_val, max_val, _, _ = cv2.minMaxLoc(gray)
    contrast = max_val - min_val
    if contrast < 30:  # Low contrast may indicate poor text visibility
        return False
    
    # Check text density (ratio of dark pixels)
    text_density = np.count_nonzero(gray < 128) / gray.size
    if text_density < 0.05:  # Too few dark pixels may indicate no text
        return False
    
    return True

def verify_japanese_text(text):
    """
    Verify if the detected text is likely valid Japanese.
    This function performs two main checks:
    1. Percentage of Japanese characters
    2. Character repetition check to avoid false positives
    
    Args:
        text (str): The text to verify
        
    Returns:
        bool: True if the text appears to be valid Japanese, False otherwise
    """
    # Find all Japanese characters in the text
    japanese_chars = re.findall(r'[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text)
    
    # Check if at least 50% of the text consists of Japanese characters
    if len(japanese_chars) < len(text) * 0.5:
        return False
    
    # Check for excessive character repetition (may indicate OCR error)
    for char in set(text):
        if text.count(char) > len(text) * 0.7:  # If any character appears more than 70% of the time
            return False
    
    return True

# Initialize the Manga OCR model
mocr = MangaOcr() 