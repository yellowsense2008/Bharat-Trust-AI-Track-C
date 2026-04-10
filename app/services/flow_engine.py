"""
flow_engine.py
Rule-based, 4-step complaint intake flow controller.

FLOW:
  Step 1 → detect_category
  Step 2 → ask_subcategory
  Step 3 → extract_amount_time
  Step 4 → confirm_issue

Replies are generated from language templates to avoid
machine-translated awkward sentences.
"""

import re
from app.services import extraction_service


# ─── Flow map ─────────────────────────────────────────────────

FLOW = {
    1: "detect_category",
    2: "ask_subcategory",
    3: "extract_amount_time",
    4: "confirm_issue",
}


# ─── Reply templates (multilingual responses) ───────────────

REPLY_TEMPLATES = {

    "payment_type": {
        "en": "What type of payment was it? (UPI / Card / Net Banking / Loan)",
        "hi": "आपका पेमेंट किस प्रकार का था? (UPI / कार्ड / नेट बैंकिंग / लोन)",
        "gu": "તમારું પેમેન્ટ કઈ રીતે કર્યું હતું? (UPI / કાર્ડ / નેટ બેન્કિંગ / લોન)",
        "ta": "நீங்கள் எந்த வகையான பணம் செலுத்தினீர்கள்? (UPI / கார்டு / நெட் பேங்கிங் / லோன்)",
        "kn": "ನೀವು ಯಾವ ರೀತಿಯ ಪಾವತಿ ಮಾಡಿದ್ದಿರಿ? (UPI / ಕಾರ್ಡ್ / ನೆಟ್ ಬ್ಯಾಂಕಿಂಗ್ / ಸಾಲ)"
    },

    "not_understood": {
        "en": "I did not understand. Is your complaint related to payment or UPI?",
        "hi": "मुझे समझ नहीं आया. क्या आपकी शिकायत पेमेंट या UPI से जुड़ी है?",
        "gu": "મને સમજાયું નહીં. શું તમારી ફરિયાદ પેમેન્ટ અથવા UPI વિશે છે?",
        "ta": "எனக்கு புரியவில்லை. உங்கள் புகார் பணம் அல்லது UPI தொடர்பானதா?",
        "kn": "ನನಗೆ ಅರ್ಥವಾಗಲಿಲ್ಲ. ನಿಮ್ಮ ದೂರು ಪಾವತಿ ಅಥವಾ UPIಗೆ ಸಂಬಂಧಿತವೇ?"
    },

    "ask_amount_time": {
        "en": "What was the amount and when did it fail? (Example: ₹500 yesterday)",
        "hi": "राशि कितनी थी और कब फेल हुआ? (जैसे ₹500 कल)",
        "gu": "રકમ કેટલી હતી અને ક્યારે ફેલ થયું? (ઉદાહરણ: ₹500 કાલે)",
        "ta": "தொகை எவ்வளவு மற்றும் எப்போது தோல்வியடைந்தது? (உதாரணம்: ₹500 நேற்று)",
        "kn": "ಮೊತ್ತ ಎಷ್ಟು ಮತ್ತು ಯಾವಾಗ ವಿಫಲವಾಯಿತು? (ಉದಾಹರಣೆ: ₹500 ನಿನ್ನೆ)"
    },

    "ask_issue": {
        "en": "Was the amount debited or is the transaction pending?",
        "hi": "क्या राशि डेबिट हो गई या ट्रांजैक्शन पेंडिंग है?",
        "gu": "શું રકમ ડેબિટ થઈ ગઈ કે ટ્રાન્ઝેક્શન પેન્ડિંગ છે?",
        "ta": "தொகை உங்கள் கணக்கில் பிடிக்கப்பட்டதா அல்லது பரிவர்த்தனை நிலுவையில் உள்ளதா?",
        "kn": "ಮೊತ್ತ ನಿಮ್ಮ ಖಾತೆಯಿಂದ ಡೆಬಿಟ್ ಆಗಿದೆಯೇ ಅಥವಾ ವ್ಯವಹಾರ ಬಾಕಿಯಿದೆಯೇ?"
    },

    "complaint_registered": {
        "en": "Complaint registered successfully. Your issue has been recorded.",
        "hi": "आपकी शिकायत सफलतापूर्वक दर्ज कर ली गई है।",
        "gu": "તમારી ફરિયાદ સફળતાપૂર્વક નોંધાઈ ગઈ છે.",
        "ta": "உங்கள் புகார் வெற்றிகரமாக பதிவு செய்யப்பட்டது.",
        "kn": "ನಿಮ್ಮ ದೂರು ಯಶಸ್ವಿಯಾಗಿ ದಾಖಲಿಸಲಾಗಿದೆ."
    },

    "already_registered": {
        "en": "Your complaint has already been registered.",
        "hi": "आपकी शिकायत पहले ही दर्ज हो चुकी है।",
        "gu": "તમારી ફરિયાદ પહેલેથી નોંધાઈ ગઈ છે.",
        "ta": "உங்கள் புகார் ஏற்கனவே பதிவு செய்யப்பட்டுள்ளது.",
        "kn": "ನಿಮ್ಮ ದೂರು ಈಗಾಗಲೇ ದಾಖಲಿಸಲಾಗಿದೆ."
    },

    "invalid_session": {
        "en": "Invalid session state. Please start again.",
        "hi": "सेशन अमान्य है। कृपया फिर से शुरू करें।",
        "gu": "સેશન અમાન્ય છે. કૃપા કરીને ફરી શરૂ કરો.",
        "ta": "செஷன் தவறானது. தயவுசெய்து மீண்டும் தொடங்குங்கள்.",
        "kn": "ಸೆಷನ್ ಅಮಾನ್ಯವಾಗಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಾರಂಭಿಸಿ."
    }
}


def get_reply(session, key):
    language = session.get("language", "en")
    return REPLY_TEMPLATES[key].get(language, REPLY_TEMPLATES[key]["en"])


# ─── Hinglish normalisation table ─────────────────────────────

_HINGLISH_MAP: dict[str, str] = {
    "mera payment fail ho gaya": "payment failed",
    "paisa nahi aaya": "money not received",
    "paise nahi aaye": "money not received",
    "transaction fail": "transaction failed",
    "paise kat gaye": "amount deducted",
    "upi fail": "upi failed",
    "nahi mila": "not received",
}


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    for hindi, english in sorted(_HINGLISH_MAP.items(), key=lambda x: -len(x[0])):
        text = text.replace(hindi, english)
    return text


# ─── Payment keyword detection ───────────────────────────────

_PAYMENT_KEYWORDS = {
    "payment", "upi", "money", "transfer",
    "paytm", "gpay", "phonepe",
    "rupees", "rupee", "₹",
    "debit", "credit", "transaction", "bank"
}


def _detect_category(text: str) -> str | None:
    tokens = set(re.findall(r"\w+", text.lower()))
    if tokens & _PAYMENT_KEYWORDS:
        return "Payments"
    return None


# ─── Core dispatcher ─────────────────────────────────────────

def process_step(session: dict, raw_message: str) -> dict:

    message = normalize_text(raw_message)
    step = session["step"]

    if session.get("completed"):
        return {
            "reply": get_reply(session, "already_registered"),
            "next_step": step,
            "completed": True,
            "meta": {"confidence": 1.0, "source": "rule"},
            "complaint": None,
        }

    # Step 1
    if step == 1:

        category = _detect_category(message)

        if category:
            session["data"]["category"] = category
            session["step"] = 2

            return {
                "reply": get_reply(session, "payment_type"),
                "next_step": 2,
                "completed": False,
                "meta": {"confidence": 0.9, "source": "rule"},
                "complaint": None,
            }

        else:
            return {
                "reply": get_reply(session, "not_understood"),
                "next_step": 1,
                "completed": False,
                "meta": {"confidence": 0.0, "source": "rule"},
                "complaint": None,
            }

    # Step 2
    elif step == 2:

        session["data"]["subcategory"] = raw_message.strip()
        session["step"] = 3

        return {
            "reply": get_reply(session, "ask_amount_time"),
            "next_step": 3,
            "completed": False,
            "meta": {"confidence": 1.0, "source": "rule"},
            "complaint": None,
        }

    # Step 3
    elif step == 3:

        extracted = extraction_service.extract_amount_time(raw_message)

        session["data"]["amount"] = extracted.get("amount")
        session["data"]["time"] = extracted.get("time")
        session["step"] = 4

        return {
            "reply": get_reply(session, "ask_issue"),
            "next_step": 4,
            "completed": False,
            "meta": {
                "confidence": extracted.get("confidence", 0.8),
                "source": extracted.get("source", "rule"),
            },
            "complaint": None,
        }

    # Step 4
    elif step == 4:

        from app.services.complaint_builder import build_complaint

        session["data"]["issue"] = raw_message.strip()
        session["completed"] = True

        complaint = build_complaint(session["data"])

        return {
            "reply": get_reply(session, "complaint_registered"),
            "next_step": 4,
            "completed": True,
            "meta": {"confidence": 1.0, "source": "rule"},
            "complaint": complaint,
        }

    else:
        return {
            "reply": get_reply(session, "invalid_session"),
            "next_step": step,
            "completed": False,
            "meta": {"confidence": 0.0, "source": "rule"},
            "complaint": None,
        }