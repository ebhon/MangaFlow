# Import required libraries for YOLO model and image processing
from ultralytics import YOLO
import cv2

def load_yolo_model(model_path):
    """
    Load the YOLO model for text detection.
    This function initializes the YOLO model that will be used to detect text regions in manga pages.
    
    Args:
        model_path (str): Path to the trained YOLO model weights file
        
    Returns:
        YOLO: Initialized YOLO model ready for inference
    """
    return YOLO(model_path)

def detect_text_regions(model, image_path):
    """
    Run YOLO inference on the image to detect text regions.
    This function processes an image through the YOLO model to identify areas containing text.
    
    Args:
        model (YOLO): The loaded YOLO model
        image_path (str): Path to the image file to process
        
    Returns:
        list: Detection results containing bounding boxes and class predictions
    """
    return model(image_path)

def sort_bubbles(boxes):
    """
    Sorts text bubbles in reading order (top-to-bottom, right-to-left).
    This function organizes detected text regions in a way that matches manga reading order.
    
    Args:
        boxes (list): List of bounding boxes from YOLO detection
        
    Returns:
        list: Sorted bounding boxes in reading order
    """
    # Sort boxes by vertical position (y-coordinate) in groups of 50 pixels
    # Within each group, sort by horizontal position (x-coordinate) in reverse order
    return sorted(boxes, key=lambda b: (int(b[1] // 50), -int(b[0])))

def determine_region_type(box, image, class_id):
    """
    Determine region type based on the model's class prediction.
    This function maps the numerical class ID to a human-readable region type.
    
    Args:
        box (tuple): Bounding box coordinates
        image (numpy.ndarray): The input image
        class_id (int): The class ID predicted by the model
        
    Returns:
        str: The type of region detected (bubble, narration, text, etc.)
    """
    # Mapping of class IDs to region types
    class_to_type = {
        0: "bubble",    # Speech bubble
        1: "narration", # Narration box
        2: "other",     # Other text regions
        3: "text",      # General text
        4: "ui"         # User interface elements
    }
    return class_to_type.get(class_id, "unknown") 