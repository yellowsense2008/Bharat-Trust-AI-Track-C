from deep_translator import GoogleTranslator
import logging

logger = logging.getLogger(__name__)

def translate_text(text: str, source_lang: str, target_lang: str):
    """
    Translate text using Google Translate via deep-translator
    """
    try:
        translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        logger.info(f"Translated {source_lang} → {target_lang}")
        return translated
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return text  # Return original on failure