import json
from datetime import datetime, timezone
from pathlib import Path

# True : email has been sent by a malicious user
# False: email has been sent by a safe user
# (email1, email2, email3, email4, email5)
PHISHING_EMAIL_STATUS = (True, False, False, True, True)
A_EMAIL_OPENED: str = "mail_opened"
A_REPORT: str = "report"
A_NO_REPORT: str = "no_report"
METRICS_PATH = Path("campaign_data/metrics.json")

# Expected metrics.json structure
#
# {
#     "user_id": {
#         "email": "user@test.com",
#         "events": {
#             "email1": {
#                 "status": True/False
#                 "email_opened": "timestamp",
#                 "report": "seconds",
#                 "no_report": "seconds"
#             }
#              ...
#         }
#     }
# }
#
# Explanation:
# - user_id: unique identifier for each user
# - email: user's email address
# - events: dictionary keyed by email_id (email1, email2, ...)
# - status: boolean value True: phishing email / False: not phishing email
# - email_opened: ISO timestamp when the email was opened
# - report: seconds between email_opened and when the user reported the phishing email
# - no_report: seconds between email_opened and when the user clicked "not phishing"


def load_metrics():
    if not METRICS_PATH.exists():
        return {}
    with open(METRICS_PATH, "r") as f:
        return json.load(f)

def save_metrics(data):
    with open(METRICS_PATH, "w") as f:
        json.dump(data, f, indent=4)

def ensure_user(data, user_id):
    data.setdefault(user_id, {
        "email": None,
        "events": {}
    })

def ensure_email_event(data, user_id, email_id):
    data[user_id]["events"].setdefault(email_id, {"status": PHISHING_EMAIL_STATUS[int(email_id)-1]})


def tracking_events(user_id: str, action: str, email_id: str):
    data = load_metrics()
    ensure_user(data, user_id)
    ensure_email_event(data, user_id, email_id)

    event_data = data[user_id]["events"][email_id]
    now = datetime.now(timezone.utc)

    # -------- EMAIL OPENED --------
    if action == A_EMAIL_OPENED:
        # Record only the first time they open it
        if A_EMAIL_OPENED not in event_data:
            event_data[A_EMAIL_OPENED] = now.isoformat()

    # -------- REPORT / NO_REPORT --------
    elif action in [A_REPORT, A_NO_REPORT]:
        # If they already clicked either button previously, do nothing to the metrics.
        # This preserves their FIRST reaction time.
        if A_REPORT in event_data or A_NO_REPORT in event_data:
            return 

        # Fallback: If their email client blocked the tracking pixel, 
        # set the open time to "now" so the math doesn't crash.
        if A_EMAIL_OPENED not in event_data:
            event_data[A_EMAIL_OPENED] = now.isoformat()

        opened_time = datetime.fromisoformat(event_data[A_EMAIL_OPENED])
        diff = (now - opened_time).total_seconds()

        event_data[action] = diff

    else:
        raise ValueError(f"Unknown action: {action}")

    save_metrics(data)