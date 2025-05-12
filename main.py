import os
import cv2
import logging
import matplotlib.pyplot as plt
import re
from dotenv import load_dotenv
from manga_translator.config import IMAGE_DIR, MODEL_PATH, FONT_PATH, TRANSLATED_DIR
from manga_translator.image_utils import reload_and_save_images, preprocess_image, enhance_text_region
from manga_translator.detection import load_yolo_model, detect_text_regions, sort_bubbles
from manga_translator.ocr import mocr, validate_ocr_result, verify_japanese_text
from manga_translator.text_utils import clean_ocr_text, split_japanese_sentences, is_similar
from manga_translator.translation import get_translator_deepl, clean_and_translate_text, post_process_translation
from manga_translator.overlay import insert_translation, check_and_fix_truncated_text

# Load environment variables from .env
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # 1. Reload and clean images
    reload_and_save_images(IMAGE_DIR)

    # 2. Load YOLO model
    model = load_yolo_model(MODEL_PATH)

    # 3. Initialize DeepL translator using API key from environment
    deepl_api_key = os.environ.get('DEEPL_API_KEY')
    translator_deepl = get_translator_deepl(deepl_api_key)

    # 4. Process each image in the directory
    for image_file in os.listdir(IMAGE_DIR):
        if not image_file.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        image_path = os.path.join(IMAGE_DIR, image_file)
        image = cv2.imread(image_path)
        if image is None:
            logging.warning(f"Could not read image: {image_path}")
            continue

        # 5. Detect text regions
        results = detect_text_regions(model, image_path)
        sorted_boxes = sort_bubbles(results[0].boxes.xyxy)

        # 6. Process and OCR text regions (class 3 only)
        text_regions = []
        for i, (box, cls_id) in enumerate(zip(results[0].boxes.xyxy, results[0].boxes.cls)):
            cls_id = int(cls_id)
            if cls_id != 3:
                continue
            x1, y1, x2, y2 = map(int, box)
            cropped = image[y1:y2, x1:x2]
            enhanced_crop = enhance_text_region(cropped)
            pil_crop = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
            pil_crop = cv2.cvtColor(pil_crop, cv2.COLOR_BGR2RGB)
            pil_crop = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
            from PIL import Image
            pil_crop = Image.fromarray(pil_crop)
            text = mocr(pil_crop)
            is_valid = validate_ocr_result(text, cropped) and verify_japanese_text(text)
            if not is_valid:
                continue
            text_regions.append({'text': text, 'coords': (x1, y1, x2, y2), 'class': cls_id})

        # 7. Clean, split, deduplicate text
        cleaned_text_regions = []
        for i, region in enumerate(text_regions):
            cleaned_text = clean_ocr_text(region['text'])
            formatted_text = split_japanese_sentences(cleaned_text)
            if formatted_text.strip():
                cleaned_text_regions.append({'id': i, 'text': formatted_text, 'coords': region['coords']})
        region_to_sentences = {}
        for region in cleaned_text_regions:
            sentences = region['text'].split('\n')
            valid_sentences = [s for s in sentences if s.strip()]
            if valid_sentences:
                region_to_sentences[region['id']] = {'sentences': valid_sentences, 'coords': region['coords']}
        all_sentences = []
        for region_id, region_data in region_to_sentences.items():
            for sentence in region_data['sentences']:
                all_sentences.append((region_id, sentence))
        unique_sentences = []
        for i, (region_id, sentence) in enumerate(all_sentences):
            is_duplicate = False
            for _, existing_sentence in unique_sentences:
                if is_similar(sentence, existing_sentence):
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_sentences.append((region_id, sentence))

        # 8. Translate text
        translation_map = {}
        for _, sentence in unique_sentences:
            is_sfx = bool(re.search(r'[ドゴバキガ]{2,}', sentence))
            translation = clean_and_translate_text(sentence, translator_deepl)
            if translation:
                processed_translation = post_process_translation(translation, "sfx" if is_sfx else None)
                translation_map[sentence] = processed_translation

        # 9. Map translations back to regions
        region_translations = {}
        for region_id, region_data in region_to_sentences.items():
            sentences = region_data['sentences']
            translations = []
            for sentence in sentences:
                if not sentence.strip():
                    continue
                is_sfx = bool(re.search(r'[ドゴバキガ]{2,}', sentence))
                if not is_sfx and sentence.strip() in ['！', '。', '、', '．．．']:
                    continue
                if sentence in translation_map:
                    translations.append(translation_map[sentence])
                else:
                    best_match = None
                    best_score = 0
                    for original in translation_map.keys():
                        score = is_similar(sentence, original)
                        if score > best_score and score > 0.8:
                            best_score = score
                            best_match = original
                    if best_match:
                        translations.append(translation_map[best_match])
            if translations:
                combined_translation = ' '.join(translations)
                is_sfx_region = any(bool(re.search(r'[ドゴバキガ]{2,}', s)) for s in sentences)
                final_translation = post_process_translation(combined_translation, "sfx" if is_sfx_region else None)
                region_translations[region_id] = {
                    'original': "\n".join(sentences),
                    'translation': final_translation,
                    'coords': region_data['coords']
                }

        # 10. Overlay translations and save results
        translated_image = image.copy()
        os.makedirs(TRANSLATED_DIR, exist_ok=True)
        for region_id, data in region_translations.items():
            if not data['translation'].strip():
                continue
            box_coords = data['coords']
            translated_image = insert_translation(
                translated_image,
                box_coords,
                data['translation'],
                font_path=FONT_PATH
            )
        translated_image = check_and_fix_truncated_text(translated_image, region_translations)
        output_path = os.path.join(TRANSLATED_DIR, f"translated_{os.path.basename(image_path)}")
        cv2.imwrite(output_path, translated_image)
        logging.info(f"Saved translated image to: {output_path}")
        # Optionally, display results
        plt.figure(figsize=(20, 10))
        plt.subplot(1, 2, 1)
        plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        plt.title("Original Image", fontsize=16)
        plt.axis('off')
        plt.subplot(1, 2, 2)
        plt.imshow(cv2.cvtColor(translated_image, cv2.COLOR_BGR2RGB))
        plt.title("Translated Image", fontsize=16)
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(os.path.join(TRANSLATED_DIR, f"comparison_{os.path.basename(image_path)}.png"), dpi=300)
        plt.close()

if __name__ == "__main__":
    main() 