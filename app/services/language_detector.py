from lingua import Language, LanguageDetectorBuilder

# Lingua supports these reliably
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


def detect_language(text: str):
    """
    Detect language of input text.
    Returns ISO language code.
    """

    try:
        lang = detector.detect_language_of(text)

        if lang is None:
            return "en"

        return LANGUAGE_MAP.get(lang, "en")

    except Exception:
        return "en"