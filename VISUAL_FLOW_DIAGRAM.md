# Conversational Intake Engine - Visual Flow Diagram

## 🎯 Complete System Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER STARTS CONVERSATION                     │
│                                                                       │
│  User: "Oh my god my payment failed! I am so worried!"              │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    POST /conversation/start                          │
│                   (conversation_routes.py)                           │
│                                                                       │
│  • Receives user message                                            │
│  • Authenticates JWT token                                          │
│  • Calls conversation_service.start_conversation()                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EMOTION DETECTION                               │
│                  (conversation_service.py)                           │
│                                                                       │
│  Keywords detected: "oh my god", "worried"                          │
│  Emotion: DISTRESS                                                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CREATE SESSION STATE                              │
│                                                                       │
│  conversation_sessions[user_id] = {                                 │
│    "form": {                                                        │
│      "bank_name": None,                                             │
│      "transaction_type": None,                                      │
│      "transaction_amount": None,                                    │
│      "transaction_date": None,                                      │
│      "transaction_id": None,                                        │
│      "issue_description": "payment failed"  ← Extracted             │
│    },                                                               │
│    "history": [...],                                                │
│    "emotion_detected": "distress"                                   │
│  }                                                                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GROQ LLM PROCESSING                               │
│                  (call_groq_llm function)                            │
│                                                                       │
│  Model: llama-3.1-70b-versatile                                     │
│  System Prompt: "You are an empathetic AI assistant..."            │
│  User Prompt: "User message: 'Oh my god my payment failed!'"       │
│                                                                       │
│  LLM analyzes:                                                      │
│  • Emotional state → Distress detected                             │
│  • Information → "payment failed"                                  │
│  • Missing fields → bank_name, transaction_type, etc.              │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LLM RESPONSE (JSON)                               │
│                                                                       │
│  {                                                                  │
│    "empathy_message": "I understand this must be very stressful    │
│                        for you. Don't worry, I'm here to help.",   │
│    "extracted_data": {                                             │
│      "issue_description": "payment failed"                         │
│    },                                                              │
│    "next_question": "Could you tell me which bank was involved?",  │
│    "is_complete": false                                            │
│  }                                                                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    RETURN TO USER                                    │
│                                                                       │
│  {                                                                  │
│    "session_id": "123",                                             │
│    "ai_response": "I understand this must be very stressful for    │
│                    you. Don't worry, I'm here to help.\n\n         │
│                    Could you tell me which bank was involved?",    │
│    "conversation_complete": false                                   │
│  }                                                                  │
└─────────────────────────────────────────────────────────────────────┘

                                 │
                                 ▼

┌─────────────────────────────────────────────────────────────────────┐
│                    USER RESPONDS                                     │
│                                                                       │
│  User: "State Bank of India"                                        │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  POST /conversation/message                          │
│                                                                       │
│  • Receives user answer                                             │
│  • Retrieves session state                                          │
│  • Calls conversation_service.continue_conversation()               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    UPDATE SESSION STATE                              │
│                                                                       │
│  conversation_sessions[user_id]["form"] = {                         │
│    "bank_name": "State Bank of India",  ← Updated                  │
│    "transaction_type": None,                                        │
│    "transaction_amount": None,                                      │
│    "transaction_date": None,                                        │
│    "transaction_id": None,                                          │
│    "issue_description": "payment failed"                            │
│  }                                                                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GROQ LLM PROCESSING                               │
│                                                                       │
│  LLM Response:                                                      │
│  {                                                                  │
│    "empathy_message": "",                                           │
│    "extracted_data": {                                             │
│      "bank_name": "State Bank of India"                            │
│    },                                                              │
│    "next_question": "What type of transaction was this?",          │
│    "is_complete": false                                            │
│  }                                                                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼

        [CONVERSATION CONTINUES FOR 5-7 MORE EXCHANGES]

                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ALL FIELDS COLLECTED                              │
│                                                                       │
│  conversation_sessions[user_id]["form"] = {                         │
│    "bank_name": "State Bank of India",                             │
│    "transaction_type": "UPI",                                       │
│    "transaction_amount": "5000 rupees",                            │
│    "transaction_date": "Today morning",                            │
│    "transaction_id": "Not provided",                               │
│    "issue_description": "Money deducted but merchant didn't get"   │
│  }                                                                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GENERATE COMPLAINT DATA                           │
│                                                                       │
│  title = "UPI Issue - State Bank of India"                         │
│  description = "Money deducted but merchant didn't get\n           │
│                 Bank: State Bank of India\n                         │
│                 Transaction Type: UPI\n                             │
│                 Amount: 5000 rupees\n                               │
│                 Date: Today morning\n                               │
│                 Transaction ID: Not provided"                       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AUTO-CREATE COMPLAINT                             │
│                  POST /complaints/ (internal)                        │
│                                                                       │
│  ComplaintCreate(                                                   │
│    title="UPI Issue - State Bank of India",                        │
│    description="..."                                                │
│  )                                                                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AI PROCESSING PIPELINE                            │
│                  (complaint_routes.py)                               │
│                                                                       │
│  1. Language Detection → English                                    │
│  2. AI Categorization → "Payment Issues"                           │
│  3. Department Routing → "Banking Operations"                      │
│  4. Priority Scoring → 8/10                                        │
│  5. Duplicate Detection → None found                               │
│  6. AI Resolution Generation → "Contact bank within 24 hours..."   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPLAINT CREATED                                 │
│                                                                       │
│  Complaint {                                                        │
│    reference_id: "GRV-2026-0001",                                   │
│    status: "submitted",                                             │
│    category: "Payment Issues",                                      │
│    department: "Banking Operations",                                │
│    priority: 8,                                                     │
│    ai_suggested_resolution: "...",                                  │
│    estimated_resolution_days: 3                                     │
│  }                                                                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    RETURN FINAL RESPONSE                             │
│                                                                       │
│  {                                                                  │
│    "conversation_complete": true,                                   │
│    "ai_response": "Thank you! Your complaint has been filed.       │
│                    Reference: GRV-2026-0001",                       │
│    "complaint": {                                                   │
│      "reference_id": "GRV-2026-0001",                               │
│      "department": "Banking Operations",                            │
│      "priority": 8,                                                 │
│      "category": "Payment Issues",                                  │
│      "expected_resolution_time": "3 days"                           │
│    },                                                               │
│    "form_data": { ... }                                             │
│  }                                                                  │
└─────────────────────────────────────────────────────────────────────┘

                                 │
                                 ▼

┌─────────────────────────────────────────────────────────────────────┐
│                    USER RECEIVES CONFIRMATION                        │
│                                                                       │
│  ✅ Complaint Filed Successfully!                                   │
│  📋 Reference ID: GRV-2026-0001                                     │
│  🏢 Department: Banking Operations                                  │
│  ⚡ Priority: 8/10                                                  │
│  📅 Expected Resolution: 3 days                                     │
│  🔍 Track Status: /complaints/timeline/GRV-2026-0001               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎤 Voice Integration Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    USER SPEAKS (VOICE INPUT)                         │
│                                                                       │
│  🎤 "Oh my god my payment failed!"                                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SPEECH-TO-TEXT (STT)                              │
│                  POST /voice/transcribe                              │
│                  (Groq Whisper API)                                  │
│                                                                       │
│  Audio → Text: "Oh my god my payment failed!"                       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  CONVERSATIONAL ENGINE                               │
│                POST /conversation/start                              │
│                                                                       │
│  [Same flow as text conversation above]                             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AI RESPONSE (TEXT)                                │
│                                                                       │
│  "I understand this must be stressful. Which bank was involved?"    │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    TEXT-TO-SPEECH (TTS)                              │
│                  POST /voice/synthesize                              │
│                  (Edge TTS)                                          │
│                                                                       │
│  Text → Audio: "I understand this must be stressful..."             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PLAY AUDIO TO USER                                │
│                                                                       │
│  🔊 AI speaks response                                              │
└─────────────────────────────────────────────────────────────────────┘

                    [LOOP CONTINUES UNTIL COMPLETE]
```

---

## 🔄 Session State Evolution

```
Step 1: Initial Message
─────────────────────────
{
  "form": {
    "bank_name": None,
    "transaction_type": None,
    "transaction_amount": None,
    "transaction_date": None,
    "transaction_id": None,
    "issue_description": "payment failed"  ← Extracted
  },
  "history": [
    {"role": "user", "content": "Oh my god my payment failed!"},
    {"role": "assistant", "content": "I understand... Which bank?"}
  ],
  "emotion_detected": "distress"
}

Step 2: Bank Name Provided
───────────────────────────
{
  "form": {
    "bank_name": "State Bank of India",  ← Updated
    "transaction_type": None,
    "transaction_amount": None,
    "transaction_date": None,
    "transaction_id": None,
    "issue_description": "payment failed"
  },
  "history": [
    {"role": "user", "content": "Oh my god my payment failed!"},
    {"role": "assistant", "content": "I understand... Which bank?"},
    {"role": "user", "content": "State Bank of India"},
    {"role": "assistant", "content": "What type of transaction?"}
  ],
  "emotion_detected": "distress"
}

Step 3-6: Continue filling...
──────────────────────────────

Step 7: All Fields Complete
────────────────────────────
{
  "form": {
    "bank_name": "State Bank of India",
    "transaction_type": "UPI",
    "transaction_amount": "5000 rupees",
    "transaction_date": "Today morning",
    "transaction_id": "Not provided",
    "issue_description": "Money deducted but merchant didn't receive"
  },
  "history": [...],
  "emotion_detected": "distress"
}

→ Auto-create complaint
→ Return reference ID
→ Clear session
```

---

## 🧠 LLM Decision Making

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LLM RECEIVES INPUT                                │
│                                                                       │
│  System Prompt: "You are an empathetic AI assistant..."            │
│  User Message: "Oh my god my payment failed!"                       │
│  Current Form: { all fields None except issue_description }         │
│  Missing Fields: [bank_name, transaction_type, ...]                │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LLM ANALYZES                                      │
│                                                                       │
│  1. Emotion Detection                                               │
│     Keywords: "oh my god", "failed"                                 │
│     → Emotion: DISTRESS                                             │
│                                                                       │
│  2. Information Extraction                                          │
│     "payment failed" → issue_description                            │
│                                                                       │
│  3. Missing Fields                                                  │
│     Priority: bank_name (most important next)                       │
│                                                                       │
│  4. Response Strategy                                               │
│     → Provide empathy first                                         │
│     → Ask for bank_name                                             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LLM GENERATES RESPONSE                            │
│                                                                       │
│  {                                                                  │
│    "empathy_message": "I understand this must be stressful...",    │
│    "extracted_data": {"issue_description": "payment failed"},      │
│    "next_question": "Which bank was involved?",                    │
│    "is_complete": false                                            │
│  }                                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow Summary

```
User Input
    ↓
Emotion Detection → Empathy Response
    ↓
LLM Processing → Information Extraction
    ↓
Session Update → Form State Updated
    ↓
Completeness Check → All fields filled?
    ↓
    ├─ No → Generate next question → Return to user
    │
    └─ Yes → Generate complaint data
              ↓
           Create complaint (POST /complaints/)
              ↓
           AI Processing Pipeline
              ↓
           Return reference ID
```

---

## 🎯 Key Components

### 1. Emotion Detection
```python
detect_emotion(text) → "frustration" | "anger" | "worry" | "distress" | None
```

### 2. LLM Processing
```python
call_groq_llm(history, message, form) → {
  "empathy_message": str,
  "extracted_data": dict,
  "next_question": str,
  "is_complete": bool
}
```

### 3. Session Management
```python
conversation_sessions[user_id] = {
  "form": dict,
  "history": list,
  "emotion_detected": str
}
```

### 4. Form Completion
```python
all_filled = all(v is not None for v in form.values())
if all_filled:
    create_complaint(title, description)
```

---

## ✅ Success Flow

```
User starts → Emotion detected → Empathy shown → Info extracted
    ↓
Questions asked → User responds → Form updated → Next question
    ↓
All fields filled → Complaint created → Reference ID returned
    ↓
User satisfied → Can track status → Issue resolved
```

---

**This visual guide shows the complete flow of the Conversational Intake Engine.**

For implementation details, see:
- `app/services/conversation_service.py`
- `app/api/conversation_routes.py`
- `CONVERSATIONAL_INTAKE_README.md`
