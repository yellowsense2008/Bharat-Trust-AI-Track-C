def generate_auto_response(complaint):

    resolution_time = "72 hours"

    if complaint.priority_score >= 8:
        resolution_time = "24 hours"
    elif complaint.priority_score >= 5:
        resolution_time = "48 hours"

    message = (
        f"Your complaint '{complaint.title}' has been registered successfully. "
        f"It has been routed to the {complaint.assigned_department}. "
        f"Priority Score: {complaint.priority_score}. "
        f"Expected resolution time: {resolution_time}."
    )

    return {
        "reference_id": complaint.reference_id,
        "message": message,
        "department": complaint.assigned_department,
        "priority": complaint.priority_score,
        "expected_resolution_time": resolution_time
    }