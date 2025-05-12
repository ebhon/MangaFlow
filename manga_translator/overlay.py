import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import logging
from manga_translator.text_utils import smart_wrap  # For text wrapping based on font size and box width

def insert_translation(image, box_coords, translated_text, font_path='font/CC Wild Words Roman.ttf', font_size_multiplier=1.0):
    """
    Insert translated text into a text region with more dynamic font sizing.
    """
    # Unpack bounding box coordinates and calculate region size
    x1, y1, x2, y2 = map(int, box_coords)
    region_width, region_height = x2 - x1, y2 - y1

    # Extract the region and create a clean white canvas of the same size
    region = image[y1:y2, x1:x2].copy()
    clean_region = np.ones_like(region) * 255  # white background

    # Convert to PIL image for flexible font drawing
    pil_region = Image.fromarray(cv2.cvtColor(clean_region, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_region)

    # Estimate a base font size from the region dimensions
    base_font_size = int(min(region_height / 4, region_width / 8))

    # Adjust font size based on how long the text is relative to the area
    text_length_factor = len(translated_text) / (region_width * region_height / 8000)
    adjusted_font_size = int(base_font_size / (1 + text_length_factor * 0.2))

    # Enforce font size boundaries (not too small or too large)
    min_size = max(14, int(region_height / 12))
    max_size = int(min(region_height / 3, region_width / 6))
    font_size = max(min_size, min(int(adjusted_font_size * font_size_multiplier * 1.2), max_size))

    # Try to load the specified font; fallback to default if missing
    try:
        font = ImageFont.truetype(font_path, font_size)
    except IOError:
        logging.warning(f"Font {font_path} not found, using default font")
        font = ImageFont.load_default()

    # Define inner padding to prevent text from touching the box edges
    padding_x = int(region_width * 0.04)
    padding_y = int(region_height * 0.04)
    effective_width = region_width - (2 * padding_x)
    effective_height = region_height - (2 * padding_y)

    # Estimate how many characters per line to wrap around properly
    avg_char_width = font_size * 0.6
    chars_per_line = int((effective_width * 0.95) / avg_char_width)

    # Wrap the translated text to fit inside the box
    wrapped_text = smart_wrap(translated_text, width=max(1, chars_per_line))

    # Measure the bounding box of the wrapped text
    text_bbox = draw.textbbox((0, 0), wrapped_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # If the text still doesn't fit, reduce font size accordingly
    if text_height > effective_height:
        reduction_factor = effective_height / text_height
        new_font_size = max(min_size, int(font_size * reduction_factor * 0.95))
        font = ImageFont.truetype(font_path, new_font_size)
        wrapped_text = smart_wrap(translated_text, width=max(1, chars_per_line))
        text_bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

    # Center the text inside the region
    text_x = (region_width - text_width) // 2
    text_y = (region_height - text_height) // 2

    # Draw the final translated text onto the region
    draw.text((text_x, text_y), wrapped_text, font=font, fill=(0, 0, 0))

    # Convert the updated region back to OpenCV format and replace in the original image
    result_region = cv2.cvtColor(np.array(pil_region), cv2.COLOR_RGB2BGR)
    image[y1:y2, x1:x2] = result_region
    return image

def check_and_fix_truncated_text(image, region_translations):
    """
    Enhanced function to fix text issues with better detection and handling for text class regions.
    """
    fixed_image = image.copy()
    text_regions = []

    # Loop through all detected regions with translations
    for region_id, data in region_translations.items():
        if not data['translation'].strip():
            continue  # skip empty translations

        # Extract coordinates and calculate size-related features
        x1, y1, x2, y2 = map(int, data['coords'])
        translation = data['translation']
        region_width = x2 - x1
        region_height = y2 - y1
        region_area = region_width * region_height
        text_length = len(translation)
        chars_per_area = text_length / max(1, region_area)

        # Classify region shape/density
        is_small_region = region_area < 15000
        is_wide_region = region_width > region_height * 1.5
        is_tall_region = region_height > region_width * 1.5
        is_dense_text = chars_per_area > 0.002

        # Set font size multiplier and rendering priority based on conditions
        font_multiplier = 1.0
        priority = 0
        if is_small_region:
            font_multiplier = 1.25
            priority = 3
        elif is_wide_region and is_dense_text:
            font_multiplier = 1.2
            priority = 2
        elif is_tall_region:
            font_multiplier = 0.9
            priority = 2
        elif is_dense_text:
            font_multiplier = 0.95
            priority = 1

        # Save region info with rendering hints
        text_regions.append({
            'region_id': region_id,
            'data': data,
            'font_multiplier': font_multiplier,
            'priority': priority,
            'area': region_area
        })

    # Sort regions by priority and size (larger areas first)
    text_regions.sort(key=lambda x: (x['priority'], -x['area']), reverse=True)

    # Insert translations into each region with adjusted font size
    for region in text_regions:
        region_id = region['region_id']
        data = region['data']
        font_multiplier = region['font_multiplier']
        fixed_image = insert_translation(
            fixed_image,
            data['coords'],
            data['translation'],
            font_path='font/CC Wild Words Roman.ttf',
            font_size_multiplier=font_multiplier
        )

    return fixed_image
