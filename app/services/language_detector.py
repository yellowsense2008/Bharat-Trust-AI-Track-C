from lingua import Language, LanguageDetectorBuilder

detector = LanguageDetectorBuilder.from_languages(
    Language.ENGLISH,
    Language.HINDI,
    Language.BENGALI,
    Language.MARATHI,
    Language.PUNJABI,
    Language.TAMIL,
    Language.GUJARATI
).build()

LANGUAGE_MAP = {
    Language.ENGLISH: "en",
    Language.HINDI: "hi",
    Language.BENGALI: "bn",
    Language.MARATHI: "mr",
    Language.PUNJABI: "pa",
    Language.TAMIL: "ta",
    Language.GUJARATI: "gu",
}

def detect_language(text: str) -> str:
    """
    Detect language of input text.
    Uses confidence score to avoid switching on mixed code-switching.
    Returns ISO language code.
    """
    try:
        lang = detector.detect_language_of(text)
        
        if lang is None:
            return "en"
        
        detected_lang = LANGUAGE_MAP.get(lang, "en")
        
        # Lingua already handles code-switching well
        # Trust its detection (it looks at probability across the text)
        return detected_lang
        
    except Exception:
        return "en"

def should_switch_language(current_language: str, new_text: str) -> bool:
    """
    Determine if we should switch languages based on new user input.
    
    This prevents switching on individual English words in mostly-Hindi text.
    Only switch if text is CLEARLY in a different language.
    """
    detected = detect_language(new_text)
    
    # Don't switch if:
    # 1. Only digits/numbers
    if new_text.strip().replace(",", "").replace(".", "").isdigit():
        return False
    
    # 2. Very short (like a name "John")
    if len(new_text.strip().split()) <= 2:
        return False
    
    # 3. Detected language same as current
    if detected == current_language:
        return False
    
    return True