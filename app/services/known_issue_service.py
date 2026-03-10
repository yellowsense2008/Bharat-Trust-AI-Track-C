from typing import Optional

# Simple known issue patterns
KNOWN_ISSUES = [
    {
        "keywords": ["upi down", "upi not working", "upi failure", "upi payment failed"],
        "message": "UPI services are currently experiencing downtime. Please try again after some time.",
        "category": "Payments"
    },
    {
        "keywords": ["server down", "app not opening", "bank app down"],
        "message": "The banking application is currently undergoing maintenance. Please try again later.",
        "category": "System"
    },
    {
        "keywords": ["otp not received", "otp delay"],
        "message": "OTP delivery may be delayed due to network congestion. Please wait a few minutes.",
        "category": "Authentication"
    }
]


def detect_known_issue(text: str) -> Optional[dict]:

    text = text.lower()

    for issue in KNOWN_ISSUES:
        for keyword in issue["keywords"]:
            if keyword in text:
                return issue

    return None