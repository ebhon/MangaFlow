import re
from difflib import SequenceMatcher
import textwrap

def clean_ocr_text(text):
    """
    Clean OCR text by removing non-Japanese/non-English characters and normalizing spaces.
    """
    # Keep only Japanese, full-width, Latin, digits, and common punctuation
    text = re.sub(r'[^\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uFF00-\uFFEFa-zA-Z0-9\s.,!?\'\"-]', '', text)
    # Remove unnecessary spaces between Kanji characters
    text = re.sub(r'(?<=[\u4E00-\u9FFF]) (?=[\u4E00-\u9FFF])', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def split_japanese_sentences(text):
    """
    Split Japanese text into sentences based on punctuation.
    """
    # Insert newlines after Japanese sentence-ending punctuation
    return re.sub(r'([。！？])', r'\1\n', text).strip()

def is_similar(a, b, threshold=0.8):
    """
    Check if two strings are similar based on sequence matching.
    """
    # Use difflib's SequenceMatcher to compare similarity
    return SequenceMatcher(None, a, b).ratio() > threshold

def manga_style_formatting(text):
    """
    Apply universal manga-specific formatting rules.
    """

    # Honorifics commonly used in manga
    manga_terms = {
        'sama': '-sama',
        'san': '-san',
        'kun': '-kun',
        'chan': '-chan',
        'sensei': '-sensei',
        'senpai': '-senpai',
        'kouhai': '-kouhai',
        'dono': '-dono',
        'shi': '-shi',
    }

    # Mapping Japanese character names to English equivalents
    character_names = {
        'カイドウ': 'Kaido',
        'モンキー・ロ・ルフィ': 'Monkey D. Luffy',
        '海賊王': 'Pirate King'
    }

    # Mapping of common Japanese words/phrases to their English manga-style translations
    phrase_map = {
        'お前': 'you',
        'おれ': 'I',
        '俺': 'I',
        'あいつ': 'that guy',
        'ばか': 'idiot',
        'くそ': 'damn',
        'ちくしょう': 'shit',
        'なに': 'what',
        'なにぃ': 'whaaat',
        'やった': 'hell yeah',
        'うるさい': 'shut up',
        'やれやれ': 'good grief',
        'はい': 'yeah',
        'いいえ': 'nah',
    }

    formatted_text = text

    # Replace Japanese character names with English equivalents
    for jp, en in character_names.items():
        formatted_text = formatted_text.replace(jp, en)

    # Replace known Japanese phrases with English translations
    for jp, en in phrase_map.items():
        formatted_text = formatted_text.replace(jp, en)

    # Replace honorifics like 'san', 'chan' with '-san', '-chan' etc.
    for key, val in manga_terms.items():
        formatted_text = re.sub(rf'\b{key}\b', val, formatted_text, flags=re.IGNORECASE)

    # Replace multiple dots with ellipses and normalize excessive punctuation
    formatted_text = formatted_text.replace('...', '…')
    formatted_text = re.sub(r'([!?]){2,}', r'\1', formatted_text)
    formatted_text = re.sub(r'\?+!+|\!+\?+', '?!', formatted_text)
    formatted_text = re.sub(r'(?<!\.)\.\.(?!\.)', '…', formatted_text)

    # Convert to uppercase if text contains an exclamation mark (shouting emphasis)
    if '!' in formatted_text:
        formatted_text = formatted_text.upper()

    return formatted_text

def smart_wrap(text, width):
    """
    Wrap text with better handling of long words.
    """
    wrapped = textwrap.fill(text, width=width)  # Initial wrapping
    lines = wrapped.split('\n')
    max_line_length = max([len(line) for line in lines]) if lines else 0

    # If any line exceeds allowed threshold, manually split long words
    if max_line_length > width * 1.2:
        new_lines = []
        for line in lines:
            if len(line) > width * 1.2:
                words = line.split()
                new_line = ""
                for word in words:
                    # Break long words by inserting hyphens
                    if len(word) > width // 2:
                        parts = [word[i:i+width//2] for i in range(0, len(word), width//2)]
                        new_line += " " + "-".join(parts)
                    else:
                        new_line += " " + word
                new_lines.append(new_line.strip())
            else:
                new_lines.append(line)
        wrapped = "\n".join(new_lines)
        wrapped = textwrap.fill(wrapped, width=width)
    return wrapped
