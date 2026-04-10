from app.services.language_service import detect_language, get_question
import re

conversation_sessions = {}


def detect_issue_type(text: str):

    text = text.lower()

    payment_keywords = ["payment", "upi", "transaction", "deducted", "money"]
    atm_keywords = ["atm", "card stuck", "machine"]

    if any(word in text for word in atm_keywords):
        return "atm"

    if any(word in text for word in payment_keywords):
        return "payment"

    return "general"


def start_conversation(user_id, initial_text):

    lang = detect_language(initial_text)
    issue_type = detect_issue_type(initial_text)

    conversation_sessions[user_id] = {
        "step": 0,
        "lang": lang,
        "issue_type": issue_type,
        "data": {
            "issue": initial_text,
            "payment_type": None,
            "bank": None,
            "amount": None,
            "date": None,
            "status": None,
            "phone": None,
            "state": None,
            "city": None
        }
    }

    return get_question(0, lang)


def continue_conversation(user_id, user_answer):

    session = conversation_sessions.get(user_id)

    if not session:
        return None

    step = session["step"]
    lang = session["lang"]
    data = session["data"]

    if step == 0:
        data["payment_type"] = user_answer

    elif step == 1:
        data["bank"] = user_answer

    elif step == 2:
        data["amount"] = user_answer

    elif step == 3:
        data["date"] = user_answer

    elif step == 4:

        status = user_answer.lower()

        if "deduct" in status:
            data["status"] = "Deducted"

        elif "pending" in status:
            data["status"] = "Pending"

        else:
            data["status"] = user_answer

    elif step == 5:

        phone = re.sub(r"\D", "", user_answer)

        if len(phone) >= 10:
            data["phone"] = phone
        else:
            data["phone"] = user_answer

    elif step == 6:
        data["state"] = user_answer

    elif step == 7:
        data["city"] = user_answer

    session["step"] += 1

    if session["step"] >= 8:

        description = (
            f"{data['issue']}. "
            f"Payment Type: {data['payment_type']}. "
            f"Bank: {data['bank']}. "
            f"Amount: {data['amount']}. "
            f"Transaction Date: {data['date']}. "
            f"Transaction Status: {data['status']}. "
            f"Phone: {data['phone']}. "
            f"State: {data['state']}. "
            f"City/District: {data['city']}."
        )

        # Better complaint title
        title = f"{data['payment_type']} Transaction Issue"

        conversation_sessions.pop(user_id)

        return {
            "complete": True,
            "title": title,
            "description": description
        }

    return get_question(session["step"], lang)