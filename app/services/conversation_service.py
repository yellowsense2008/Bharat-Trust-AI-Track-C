"""conversation_service.py
Conversational Complaint Intake Engine with emotion detection,
empathetic responses, and dynamic form loading from JSON files.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Optional, List
import google.generativeai as genai

# Initialize Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL_NAME = "gemini-2.5-flash"

conversation_sessions: Dict[int, Dict] = {}

# Path to forms directory
FORMS_DIR = Path(__file__).parent.parent / "forms"

def load_bank_form(bank_name: str) -> Optional[Dict]:
    """Load bank-specific form from JSON file."""
    form_file = FORMS_DIR / f"{bank_name.lower()}_form.json"
    
    if not form_file.exists():
        return None
    
    try:
        with open(form_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading form {form_file}: {e}")
        return None

def create_empty_form(form_config: Dict) -> Dict:
    """Create empty form dictionary from form configuration."""
    form = {"bank_name": form_config["bank_name"]}
    for field in form_config["fields"]:
        form[field["name"]] = None
    return form

def get_required_fields(form_config: Dict) -> List[str]:
    """Get list of required field names from form configuration."""
    return [field["name"] for field in form_config["fields"] if field["required"]]

def _clean_llm_text(text: str) -> str:
    """Strip markdown code blocks from plain-text Gemini responses."""
    text = re.sub(r"```[a-z]*\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    return text.strip()

def get_field_question(form_config: Dict, field_name: str) -> str:
    """Get the question text for a specific field."""
    for field in form_config["fields"]:
        if field["name"] == field_name:
            return field.get("question", f"Please provide {field['label']}")
    return f"Please provide {field_name}"

# Bank name normalization mapping
BANK_MAPPING = {
    "sbi": ["sbi", "state bank of india", "state bank"],
    "hdfc": ["hdfc", "hdfc bank"],
    "icici": ["icici", "icici bank"],
    "axis": ["axis", "axis bank"],
    "kotak": ["kotak", "kotak mahindra", "kotak mahindra bank"],
    "pnb": ["pnb", "punjab national bank", "punjab national"],
    "bob": ["bob", "bank of baroda", "baroda"],
    "canara": ["canara", "canara bank"],
    "union": ["union", "union bank", "union bank of india"],
    "idbi": ["idbi", "idbi bank"],
    "yes": ["yes", "yes bank"],
    "indusind": ["indusind", "indusind bank"],
}

def normalize_bank_name(text: str) -> str:
    """Normalize user input to canonical bank name (accept ANY bank)."""
    text_lower = text.lower().strip()
    
    for canonical_name, keywords in BANK_MAPPING.items():
        if any(kw in text_lower for kw in keywords):
            return canonical_name
    
    if "other" in text_lower:
        return "other"
    
    # Accept any bank name (even if unknown)
    normalized = ''.join(c for c in text_lower if c.isalnum() or c == ' ')
    return normalized.strip().replace(' ', '_').lower() or "unknown_bank"

def detect_bank(text: str) -> Optional[str]:
    """Detect bank name from user message."""
    text_lower = text.lower().strip()
    for canonical_name, keywords in BANK_MAPPING.items():
        if any(kw in text_lower for kw in keywords):
            return canonical_name
    return None

SYSTEM_PROMPT = """You are an empathetic AI assistant helping citizens file banking complaints.

CRITICAL LANGUAGE RULE: Always respond in the SAME language the user is writing in.
- If user writes in Hindi, respond in Hindi
- If user writes in English, respond in English
- If user mixes Hindi and English, respond in Hindi
- Never switch languages mid-conversation

Your responsibilities:
1. COMFORT FIRST: Detect emotional distress and respond with genuine empathy
2. AUTO-EXTRACT: Extract ALL information from user's natural language automatically
3. ASK MINIMAL: Only ask for missing required fields, one at a time
4. BE HUMAN: Sound conversational, not robotic or interrogative

IMPORTANT - Auto-extraction examples:
- "Yesterday I sent 500 rupees through UPI" → extract: amount=500, transaction_type=UPI, transaction_date=yesterday
- "My name is Raj and my number is 9876543210" → extract: customer_name=Raj, mobile_number=9876543210
- "Transaction ID was TXN123456" → extract: transaction_id=TXN123456

Response format (JSON):
{
  "empathy_message": "Brief empathetic response if user is distressed, else empty",
  "extracted_data": {"field_name": "value", ...},
  "next_question": "Question for ONE missing required field, or empty if all collected",
  "is_complete": false
}

Rules:
- Extract EVERYTHING you can from each message
- If user expresses emotion, acknowledge it warmly
- Ask for ONE missing required field at a time
- When all required fields collected, set is_complete to true
- Be conversational: "What's your name?" not "Please provide customer name"
"""

def detect_emotion(text: str) -> Optional[str]:
    """Detect emotional keywords in user message across multiple languages."""
    text_lower = text.lower()
    
    # English emotions
    emotions = {
        "frustration": ["frustrated", "annoying", "irritating", "fed up"],
        "anger": ["angry", "furious", "outraged", "mad"],
        "worry": ["worried", "concerned", "anxious", "scared", "afraid"],
        "distress": ["help", "urgent", "emergency", "please", "oh my god", "omg"]
    }
    
    # Hindi emotions (Devanagari)
    hindi_emotions = {
        "worry": ["डर", "चिंता", "परेशान", "घबरा"],  # dar, chinta, pareshan, ghabra
        "distress": ["भगवान", "मदद", "बचाओ", "प्लीज"],  # bhagwan, madad, bachao, please
        "anger": ["गुस्सा", "क्रोध"],  # gussa, krodh
    }
    
    # Tamil emotions
    tamil_emotions = {
        "worry": ["பயம்", "கவலை", "பதற்றம்"],  # bayam, kavalai, pathattam
        "distress": ["கடவுளே", "உதவி", "காப்பாற்று"],  # kadavule, uthavi, kappatru
    }
    
    # Gujarati emotions
    gujarati_emotions = {
        "worry": ["ડર", "ચિંતા", "પરેશાન"],  # dar, chinta, pareshan
        "distress": ["ભગવાન", "મદદ", "બચાવો"],  # bhagwan, madad, bachavo
    }
    
    # Check English
    for emotion, keywords in emotions.items():
        if any(kw in text_lower for kw in keywords):
            return emotion
    
    # Check Hindi
    for emotion, keywords in hindi_emotions.items():
        if any(kw in text for kw in keywords):
            return emotion
    
    # Check Tamil
    for emotion, keywords in tamil_emotions.items():
        if any(kw in text for kw in keywords):
            return emotion
    
    # Check Gujarati
    for emotion, keywords in gujarati_emotions.items():
        if any(kw in text for kw in keywords):
            return emotion
    
    return None

def call_groq_llm(conversation_history: list, user_message: str, current_form: dict, form_config: Dict, required_fields: list, session_language: str = "en") -> dict:
    """Call Gemini LLM to process conversation and extract data intelligently."""
    
    missing_required = [field for field in required_fields if current_form.get(field) is None]
    
    # Build field descriptions with DETAILED guidance
    field_info = []
    for field_config in form_config["fields"]:
        field_name = field_config["name"]
        field_label = field_config["label"]
        field_type = field_config.get("type", "text")  # NEW: Use field type
        is_required = "REQUIRED" if field_config["required"] else "optional"
        current_value = current_form.get(field_name)
        status = f"✓ {current_value}" if current_value else "missing"
        field_info.append(f"  - {field_name} ({field_label}) [Type: {field_type}] [{is_required}]: {status}")
    
    fields_text = "\n".join(field_info)
    
    user_prompt = f"""You are helping fill out a {form_config['display_name']} complaint form.

SESSION LANGUAGE: {session_language} - ALL your responses MUST be in {session_language} language only. Do NOT use English unless session_language is "en".

FORM FIELDS DEFINITION:
{fields_text}

Current user message: "{user_message}"

CURRENT FORM STATUS:
{json.dumps(current_form, indent=2)}

MISSING REQUIRED FIELDS: {', '.join(missing_required) if missing_required else 'NONE - ALL FIELDS COMPLETE!'}

RULES FOR THIS BANK FORM:
1. Extract data EXACTLY into the field names defined above
2. Match user data to the SPECIFIC fields in this form
3. Ask for ONE missing field at a time using natural conversational language
4. When ALL required fields are filled, set is_complete to true
5. CRITICAL: Respond in {session_language} language ONLY. Do NOT switch languages.

Respond ONLY with valid JSON in this format:
{{
  "empathy_message": "short empathetic response if user is distressed, else empty string",
  "extracted_data": {{"field_name": "value", ...}},
  "next_question": "natural conversational question for ONE missing field in {session_language}, or empty if complete",
  "is_complete": false
}}"""
    
    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_PROMPT,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 1024,
                "response_mime_type": "application/json"
            }
        )
        response = model.generate_content(user_prompt)
        raw = response.text.strip()
        
        # Parse JSON - with response_mime_type set, Gemini returns pure JSON
        import re as _re
        # Remove any accidental markdown if present
        raw = _re.sub(r"```json\s*", "", raw)
        raw = _re.sub(r"```\s*", "", raw)
        raw = raw.strip()
        
        # Find matching braces properly
        def _extract_json(text):
            start = text.find("{")
            if start == -1:
                return text
            depth = 0
            for i, c in enumerate(text[start:], start):
                if c == "{": depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start:i+1]
            return text[start:]
        
        parsed = json.loads(_extract_json(raw))
        print(f"[Gemini OK] extracted={parsed.get('extracted_data')}, next_q={parsed.get('next_question')}")
        return parsed
    
    except Exception as e:
        print(f"Gemini LLM error: {e}")
        print(f"Raw content was: {raw[:200] if 'raw' in dir() else 'N/A'}")
        if missing_required:
            next_field = missing_required[0]
            question = get_field_question(form_config, next_field)
            return {"empathy_message": "", "extracted_data": {}, "next_question": question, "is_complete": False}
        return {"empathy_message": "", "extracted_data": {}, "next_question": "Could you please provide more details?", "is_complete": False}

def start_conversation(user_id: int, initial_text: str, language: str = None) -> str:
    """Start conversation with language tracking."""
    
    emotion = detect_emotion(initial_text)
    
    # Detect bank from initial message
    detected_bank = detect_bank(initial_text)

    # Import and detect language properly
    from app.services.language_detector import detect_language, should_switch_language
    
    # If language not provided, detect it
    if not language:
        language = detect_language(initial_text)
    
    # Store detected language in session (will be maintained throughout)
    detected_language = language
    
    # ALWAYS show bank selection form first (good UX)
    if not detected_bank:
        conversation_sessions[user_id] = {
            "awaiting_bank_selection": True,
            "history": [{"role": "user", "content": initial_text}],
            "emotion_detected": emotion,
            "detected_language": language,  # ✅ Track language from start
            "language_locked": False  # Only lock after confirmation
        }
        
        # Use Gemini to ask bank question in correct language
        try:
            model = genai.GenerativeModel(
                model_name=MODEL_NAME,
                system_instruction=SYSTEM_PROMPT,
                generation_config={"temperature": 0.7, "max_output_tokens": 512}
            )
            bank_prompt = f"""The user said: "{initial_text}"
They want to file a banking complaint but haven't mentioned a bank yet.
Respond in {language} language.
Ask them which bank was involved in the transaction - keep it short and conversational.
If they seem distressed, acknowledge it first.
Return ONLY the response text, no JSON."""
            bank_response = model.generate_content(bank_prompt)
            response = _clean_llm_text(bank_response.text)
        except Exception:
            response = "Which bank was your transaction with? Just type the bank name."
        
        conversation_sessions[user_id]["history"].append({"role": "assistant", "content": response})
        return response
    
    # Load bank form with fallback to SBI
    form_config = load_bank_form(detected_bank)
    if not form_config:
        # Fallback to SBI form if bank-specific form doesn't exist
        form_config = load_bank_form("sbi")
        if not form_config:
            return "Sorry, I couldn't load the complaint form. Please try again."
    
    # Create empty form and get required fields
    form_template = create_empty_form(form_config)
    required_fields = get_required_fields(form_config)
    
    conversation_sessions[user_id] = {
        "form": form_template,
        "form_config": form_config,
        "bank": detected_bank,
        "required_fields": required_fields,
        "history": [{"role": "user", "content": initial_text}],
        "emotion_detected": emotion,
        "awaiting_bank_selection": False,
        "detected_language": language
    }
    
    llm_response = call_groq_llm(
        conversation_history=[{"role": "user", "content": initial_text}],
        user_message=initial_text,
        current_form=form_template,
        form_config=form_config,
        required_fields=required_fields,
        session_language=language
    )
    
    # Update form with extracted data
    if llm_response.get("extracted_data"):
        for key, value in llm_response["extracted_data"].items():
            if key in conversation_sessions[user_id]["form"] and value:
                conversation_sessions[user_id]["form"][key] = value
    
    # Build response
    response_parts = []
    if llm_response.get("empathy_message"):
        response_parts.append(llm_response["empathy_message"])
    if llm_response.get("next_question"):
        response_parts.append(llm_response["next_question"])
    
    response = "\n\n".join(response_parts) if response_parts else "How can I help you today?"
    
    conversation_sessions[user_id]["history"].append({"role": "assistant", "content": response})
    
    return response

def continue_conversation(user_id: int, user_answer: str) -> dict:
    """Process user response and continue conversation."""
    
    session = conversation_sessions.get(user_id)
    if not session:
        return {"error": "Session not found. Please start a new conversation."}
    
    # ✅ ADD THIS: Prevent language switching
    from app.services.language_detector import detect_language, should_switch_language
    
    current_language = session.get("detected_language", "en")
    
    # Check if we should switch language
    if should_switch_language(current_language, user_answer):
        # User clearly switched to different language
        # Log it but continue in original language for now
        print(f"User may have switched languages. Detected: {detect_language(user_answer)}, Current: {current_language}")
        # OPTIONAL: You could switch here if you want to support multi-language in same session
        # For now, we keep using the detected language
    
    # ✅ END OF ADDITION

    session["history"].append({"role": "user", "content": user_answer})
    
    # Handle bank selection if awaiting
    if session.get("awaiting_bank_selection"):
        detected_bank = detect_bank(user_answer)
        
        if not detected_bank:
            # Ask again in session language
            lang = session.get("detected_language", "en")
            try:
                model = genai.GenerativeModel(
                    model_name=MODEL_NAME,
                    generation_config={"temperature": 0.7, "max_output_tokens": 100}
                )
                r = model.generate_content(f"Ask the user again which bank was involved in their transaction. Respond in {lang} language only. Keep it short. Plain text only.")
                response = _clean_llm_text(r.text)
            except Exception:
                response = "Which bank was your transaction with? Just type the bank name."
            session["history"].append({"role": "assistant", "content": response})
            return response
        
        # Load bank form with fallback to SBI
        form_config = load_bank_form(detected_bank)
        if not form_config:
            # Fallback to SBI form
            form_config = load_bank_form("sbi")
            if not form_config:
                return {"error": "Sorry, I couldn't load the complaint form. Please try again."}
        
        # Update session with bank form
        session["form"] = create_empty_form(form_config)
        session["form_config"] = form_config
        session["bank"] = detected_bank
        session["required_fields"] = get_required_fields(form_config)
        session["awaiting_bank_selection"] = False
        
        # Confirm bank loaded in session language - NO JSON system prompt
        lang = session.get("detected_language", "en")
        try:
            plain_model = genai.GenerativeModel(
                model_name=MODEL_NAME,
                generation_config={"temperature": 0.7, "max_output_tokens": 300}
            )
            r = plain_model.generate_content(f"You are a helpful banking assistant. In 2 short sentences in {lang} language, tell the user you loaded the {form_config['display_name']} form and ask their name. No JSON.")
            response = _clean_llm_text(r.text)
        except Exception:
            response = f"I've loaded the {form_config['display_name']} complaint form. What's your name?"
        session["history"].append({"role": "assistant", "content": response})
        return response
    
    llm_response = call_groq_llm(
        conversation_history=session["history"],
        user_message=user_answer,
        current_form=session["form"],
        form_config=session["form_config"],
        required_fields=session["required_fields"],
        session_language=session.get("detected_language", "en")
    )
    
    # Update form with extracted data
    if llm_response.get("extracted_data"):
        for key, value in llm_response["extracted_data"].items():
            if key in session["form"] and value:
                session["form"][key] = value
    
    # Check if all required fields are filled
    all_required_filled = all(session["form"].get(field) is not None for field in session["required_fields"])
    
    # Handle confirmation flow
    if session.get("awaiting_confirmation"):
        user_response = user_answer.lower().strip()
        
        # User confirms
        # Detect yes in multiple languages
        yes_words = ["yes", "y", "correct", "confirm", "ok", "okay", "submit", "bilkul", "theek",
                     "हाँ", "हां", "हा", "ठीक", "सही", "हाँजी",
                     "ஆம்", "ஆமாம்", "હા", "হ্যাঁ", "ਹਾਂ",
                     "ہاں", "ہان", "جی", "سممٹ"]
        no_words = ["no", "n", "update", "change", "nahi", "naa",
                    "नहीं", "नही", "ना",
                    "இல்லை", "ના", "না", "ਨਹੀਂ",
                    "نہیں"]
        if any(w in user_response for w in yes_words):
            form_data = session["form"]
            form_config = session["form_config"]
            
            title = f"{form_data.get('transaction_type', 'Transaction')} Issue - {form_config['display_name']}"
            
            description = f"""{form_data.get('complaint_description', 'Issue reported')}

--- Complaint Details ---
Bank: {form_config['display_name']}
Customer Name: {form_data.get('customer_name')}
Mobile Number: {form_data.get('mobile_number')}
Transaction Type: {form_data.get('transaction_type')}
Transaction ID: {form_data.get('transaction_id') or 'Not provided'}
Transaction Date: {form_data.get('transaction_date') or 'Not provided'}
Amount: {form_data.get('amount') or 'Not provided'}"""
            
            conversation_sessions.pop(user_id)
            
            return {
                "complete": True,
                "title": title,
                "description": description,
                "form_data": form_data,
                "user_language": session.get("detected_language", "en")
            }
        
        # User wants to update
        elif any(w in user_response for w in no_words):
            session["awaiting_confirmation"] = False
            lang = session.get("detected_language", "en")
            try:
                model = genai.GenerativeModel(model_name=MODEL_NAME, generation_config={"temperature": 0.7, "max_output_tokens": 100})
                r = model.generate_content(f"Tell the user no problem and ask which detail they want to correct. Respond in {lang} language only. Plain text only, no JSON, no markdown.")
                response = _clean_llm_text(r.text)
            except Exception:
                response = "No problem. Please tell me which detail needs to be corrected."
            session["history"].append({"role": "assistant", "content": response})
            return response
        
        # Unclear response — static safe message, no LLM call
        else:
            lang = session.get("detected_language", "en")
            response = "कृपया हाँ या नहीं में जवाब दें।" if lang == "hi" else "Please reply YES to submit or NO to update."
            session["history"].append({"role": "assistant", "content": response})
            return response
    
    if all_required_filled or llm_response.get("is_complete"):
        # Set awaiting confirmation flag
        session["awaiting_confirmation"] = True
        
        form_data = session["form"]
        form_config = session["form_config"]
        
        # Generate confirmation message in session language
        lang = session.get("detected_language", "en")
        form_summary = f"""Bank: {form_config['display_name']}
Customer Name: {form_data.get('customer_name')}
Mobile Number: {form_data.get('mobile_number')}
Transaction Type: {form_data.get('transaction_type')}
Amount: {form_data.get('amount') or 'Not provided'}
Date: {form_data.get('transaction_date') or 'Not provided'}
Transaction ID: {form_data.get('transaction_id') or 'Not provided'}
Issue: {form_data.get('complaint_description')}"""
        try:
            plain_model = genai.GenerativeModel(
                model_name=MODEL_NAME,
                generation_config={"temperature": 0.3, "max_output_tokens": 300}
            )
            r = plain_model.generate_content(
                f"Summarize this complaint for confirmation in {lang} language. "
                f"Show all the details clearly and ask if it is correct. "
                f"Tell them to say yes to submit or no to update. "
                f"Details:\n{form_summary}\n\nRespond in {lang} language only. Plain text only, no JSON, no markdown."
            )
            confirmation_msg = _clean_llm_text(r.text)
        except Exception:
            confirmation_msg = f"Please confirm your complaint details:\n\n{form_summary}\n\nIs this correct? Say YES to submit or NO to update."
        
        session["history"].append({"role": "assistant", "content": confirmation_msg})
        return confirmation_msg
    
    # Build response
    response_parts = []
    if llm_response.get("empathy_message"):
        response_parts.append(llm_response["empathy_message"])
    if llm_response.get("next_question"):
        response_parts.append(llm_response["next_question"])
    
    response = "\n\n".join(response_parts) if response_parts else "Please provide more information."
    
    session["history"].append({"role": "assistant", "content": response})
    
    return response

def get_session_state(user_id: int) -> Optional[dict]:
    """Get current session state for debugging."""
    return conversation_sessions.get(user_id)
