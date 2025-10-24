"""
Rule-based AI Bot to classify intent, extract fields, and generate clarifying questions.
Using keyword rules and regex to simulate intent classification and required-field check.
"""
import re
from db import insert_payload, update_conversation_status, get_conn
import json

# Define  services and required fields
SERVICE_RULES = {
    "Finance": {
        "keywords": ["invoice", "finance", "payment", "report", "tax"],
        "required": ["customer_id", "start_date", "end_date", "description"],
    },
    "IT": {
        "keywords": ["access", "server", "error", "bug", "login", "password"],
        "required": ["device", "error_message", "description"],
    },
    "General": {"keywords": [], "required": ["description"]},
}


def find_service(text):
    text_l = text.lower()
    for service, info in SERVICE_RULES.items():
        for kw in info["keywords"]:
            if kw.lower() in text_l:
                return service
    return "General"


def extract_fields(text):
    # Regex extraction
    fields = {}
    m = re.search(r"(?:customer id|customer):\s*([A-Za-z0-9\-]+)", text, re.I)
    if m:
        fields["customer_id"] = m.group(1)
    m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    if m:
        # First match
        dates = re.findall(r"(\d{4}-\d{2}-\d{2})", text)
        if dates:
            fields["start_date"] = dates[0]
            if len(dates) > 1:
                fields["end_date"] = dates[1]
    m = re.search(r"(error[:\s]+)(.+)", text, re.I)
    if m:
        fields["error_message"] = m.group(2).strip()
    # Description fallback: entire message
    fields["description"] = text.strip()
    return fields


def analyze_conversation(conversation_id):
    # Fetch conversation
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,))
    row = cur.fetchone()
    if not row:
        return None
    raw = row["raw_message"]
    service = find_service(raw)
    extracted = extract_fields(raw)
    required = SERVICE_RULES.get(service, SERVICE_RULES["General"])["required"]
    missing = [f for f in required if f not in extracted or not extracted.get(f)]
    payload = {
        "conversation_id": conversation_id,
        "service": service,
        "fields": extracted,
        "required": required,
        "missing": missing,
    }
    # Decide complete
    payload["complete"] = len(missing) == 0
    # If not complete generate clarifying question list
    if not payload["complete"]:
        questions = []
        for m in payload["missing"]:
            if m == "customer_id":
                questions.append("Could you share your customer ID?")
            elif m == "start_date":
                questions.append("What's the start date? (YYYY-MM-DD)")
            elif m == "end_date":
                questions.append("What's the end date? (YYYY-MM-DD)")
            elif m == "device":
                questions.append(
                    "Which device are you using (e.g., Windows laptop, iPhone)?"
                )
            elif m == "error_message":
                questions.append("Please paste the exact error message or screenshot.")
            else:
                questions.append(f"Could you provide the {m}?")
        payload["clarifying_questions"] = questions
        # Update conversation status waiting_for_info
        cur2 = conn.cursor()
        cur2.execute(
            "UPDATE conversations SET status=? WHERE id=?",
            ("waiting_for_info", conversation_id),
        )
        conn.commit()
    else:
        # Mark conversation ready
        cur2 = conn.cursor()
        cur2.execute(
            "UPDATE conversations SET status=? WHERE id=?", ("ready", conversation_id)
        )
        conn.commit()
    conn.close()
    insert_payload(conversation_id, payload)
    return payload
