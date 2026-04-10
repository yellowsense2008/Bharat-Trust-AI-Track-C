def detect_language(text: str) -> str:
    """
    Detect language using unicode ranges.
    Supported languages:
    English (en)
    Hindi (hi)
    Tamil (ta)
    Kannada (kn)
    Gujarati (gu)
    """

    for char in text:

        if "\u0900" <= char <= "\u097F":
            return "hi"

        if "\u0B80" <= char <= "\u0BFF":
            return "ta"

        if "\u0C80" <= char <= "\u0CFF":
            return "kn"

        if "\u0A80" <= char <= "\u0AFF":
            return "gu"

    return "en"


def get_question(step: int, lang: str):

    questions = {

        "en": [
            "Where did the payment fail? (UPI / Loan / Card / Net Banking)",
            "Which bank was involved? (SBI / HDFC / ICICI / Axis / Other)",
            "What was the transaction amount?",
            "When did the transaction occur?",
            "Was the transaction pending or was the money deducted?",
            "Please provide your phone number.",
            "Which state are you located in?",
            "Which city or district are you from?"
        ],

        "hi": [
            "भुगतान कहाँ विफल हुआ? (UPI / Loan / Card / Net Banking)",
            "कौन सा बैंक शामिल था? (SBI / HDFC / ICICI / Axis / Other)",
            "लेन-देन की राशि कितनी थी?",
            "लेन-देन कब हुआ था?",
            "क्या पैसा कट गया था या ट्रांजैक्शन पेंडिंग था?",
            "कृपया अपना फोन नंबर बताएं।",
            "आप किस राज्य से हैं?",
            "आप किस शहर या जिले से हैं?"
        ],

        "ta": [
            "பணம் எங்கு தோல்வியடைந்தது? (UPI / Loan / Card / Net Banking)",
            "எந்த வங்கி சம்பந்தப்பட்டது? (SBI / HDFC / ICICI / Axis / Other)",
            "பரிவர்த்தனை தொகை எவ்வளவு?",
            "பரிவர்த்தனை எப்போது நடந்தது?",
            "பணம் கழிக்கப்பட்டதா அல்லது பரிவர்த்தனை நிலுவையிலா?",
            "தயவுசெய்து உங்கள் தொலைபேசி எண்ணை வழங்கவும்.",
            "நீங்கள் எந்த மாநிலத்தைச் சேர்ந்தவர்?",
            "நீங்கள் எந்த நகரம் அல்லது மாவட்டத்தைச் சேர்ந்தவர்?"
        ],

        "kn": [
            "ಪಾವತಿ ಎಲ್ಲಲ್ಲಿ ವಿಫಲವಾಯಿತು? (UPI / Loan / Card / Net Banking)",
            "ಯಾವ ಬ್ಯಾಂಕ್ ಸಂಬಂಧಿಸಿದೆ? (SBI / HDFC / ICICI / Axis / Other)",
            "ವ್ಯವಹಾರದ ಮೊತ್ತ ಎಷ್ಟು?",
            "ವ್ಯವಹಾರ ಯಾವಾಗ ನಡೆದಿದೆ?",
            "ಹಣ ಕಡಿತವಾಗಿದೆಯಾ ಅಥವಾ ವ್ಯವಹಾರ ಬಾಕಿಯಿದೆಯಾ?",
            "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಫೋನ್ ಸಂಖ್ಯೆಯನ್ನು ನೀಡಿ.",
            "ನೀವು ಯಾವ ರಾಜ್ಯದಿಂದ ಬಂದಿದ್ದೀರಿ?",
            "ನೀವು ಯಾವ ನಗರ ಅಥವಾ ಜಿಲ್ಲೆಯಿಂದ ಬಂದಿದ್ದೀರಿ?"
        ],

        "gu": [
            "ચુકવણી ક્યાં નિષ્ફળ ગઈ? (UPI / Loan / Card / Net Banking)",
            "કઈ બેંક સંકળાયેલી હતી? (SBI / HDFC / ICICI / Axis / Other)",
            "ટ્રાન્ઝેક્શનની રકમ કેટલી હતી?",
            "ટ્રાન્ઝેક્શન ક્યારે થયું હતું?",
            "પૈસા કપાઈ ગયા હતા કે ટ્રાન્ઝેક્શન પેન્ડિંગ હતું?",
            "કૃપા કરીને તમારો ફોન નંબર આપો.",
            "તમે કયા રાજ્યમાંથી છો?",
            "તમે કયા શહેર અથવા જિલ્લામાંથી છો?"
        ]

    }

    return questions.get(lang, questions["en"])[step]