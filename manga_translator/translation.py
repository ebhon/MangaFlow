import logging
import re
import deepl
from manga_translator.text_utils import manga_style_formatting  # Custom formatting function for manga style

# Initialize the DeepL translator, or a placeholder if no valid API key is provided
def get_translator_deepl(api_key):
    """
    Initialize DeepL translator. If api_key is None or invalid, use a placeholder translator.
    The API key should be loaded from the environment (e.g., using dotenv).
    """
    if not api_key:
        logging.warning("No DeepL API key provided. Using placeholder translator.")

        # Define fallback translator that wraps text with a marker
        class PlaceholderTranslator:
            def translate_text(self, text, source_lang, target_lang, preserve_formatting=True):
                class Result:
                    def __init__(self, text):
                        self.text = f"[TRANSLATION: {text}]"
                return Result(text)

        return PlaceholderTranslator()

    try:
        return deepl.Translator(api_key)  # Try to initialize actual DeepL translator
    except Exception as e:
        logging.error(f"Failed to initialize DeepL translator: {e}")

        # Use fallback translator on error
        class PlaceholderTranslator:
            def translate_text(self, text, source_lang, target_lang, preserve_formatting=True):
                class Result:
                    def __init__(self, text):
                        self.text = f"[TRANSLATION: {text}]"
                return Result(text)

        return PlaceholderTranslator()

# Clean and translate input Japanese text into English
def clean_and_translate_text(text, translator_deepl, context=None):
    """
    Clean and translate text with universal manga context.
    """
    # Ignore punctuation-only input
    if text.strip() in ['！', '。', '、', '．．．', '？']:
        return ""

    cleaned_text = text.strip()

    try:
        # Translate text from Japanese to English
        translation = translator_deepl.translate_text(
            cleaned_text,
            source_lang='JA',
            target_lang='EN-US',
            preserve_formatting=True
        ).text

        # Apply manga-specific formatting
        translation = manga_style_formatting(translation)

        # Clean up spacing before punctuation
        translation = re.sub(r'\s+([!?.,])', r'\1', translation)
        translation = re.sub(r'[\s\n]+', ' ', translation).strip()

        logging.info(f"Translated: {cleaned_text} -> {translation}")
        return translation

    except Exception as e:
        logging.error(f"Translation failed for {cleaned_text}: {e}")
        return ""

# Add special formatting to translated text based on detected text type (e.g., SFX or emphasis)
def post_process_translation(translation, text_type=None):
    """
    Apply final formatting based on text type.
    """
    if text_type is None:
        # Auto-detect text type based on characters or punctuation
        if bool(re.search(r'[ドゴバキガ]{2,}', translation)):
            text_type = "sfx"
        elif '!' in translation or '?' in translation:
            text_type = "emphasis"

    # Format sound effects in uppercase and wrap in asterisks
    if text_type == "sfx":
        return f"*{translation.upper()}*"

    # Emphasize emotional text by uppercasing or appending punctuation
    elif text_type == "emphasis":
        if '!' in translation and '?' in translation:
            return translation.upper() + "?!"
        elif '!' in translation:
            return translation.upper()
        else:
            return translation

    # Default return
    return translation
