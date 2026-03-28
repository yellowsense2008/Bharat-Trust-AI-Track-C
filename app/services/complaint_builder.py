"""
complaint_builder.py
Assembles a structured complaint ticket from collected session data.
No external dependencies — pure business logic.
"""


def build_complaint(data: dict) -> dict:
    """
    Build a structured complaint dict from session data.

    Args:
        data: session["data"] containing category, subcategory, amount, time, issue.

    Returns:
        {
            "title": str,
            "category": str,
            "description": str,
        }
    """
    category = data.get("category") or "General"
    subcategory = data.get("subcategory") or ""
    amount = data.get("amount")
    time_info = data.get("time")
    issue = data.get("issue") or ""

    # ── Build title ───────────────────────────────────────────────────────────
    if subcategory:
        title = f"{subcategory} {category} Issue"
    else:
        title = f"{category} Issue"

    # ── Build description ─────────────────────────────────────────────────────
    parts = []

    if amount:
        parts.append(f"{category} payment of ₹{amount}")
    else:
        parts.append(f"{category} payment")

    if time_info:
        parts.append(f"failed {time_info}")
    else:
        parts.append("failed")

    if issue:
        parts.append(f"— {issue}")

    description = " ".join(parts).strip()

    return {
        "title": title.strip(),
        "category": category,
        "description": description,
    }
