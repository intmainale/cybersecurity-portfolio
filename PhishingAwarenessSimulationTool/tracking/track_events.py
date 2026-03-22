import json, csv
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
WEEKLY_METRICS_PATH = Path("reports/weekly_metrics.csv")
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


def save_metrics(data):
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_PATH, "w") as f:
        json.dump(data, f, indent=4)

def load_metrics():
    if not METRICS_PATH.exists() or METRICS_PATH.stat().st_size == 0:
        save_metrics({})
        return {}
    try:
        with open(METRICS_PATH, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        save_metrics({})
        return {}

def ensure_user(data, user_id):
    data.setdefault(user_id, {
        "events": {}
    })

def ensure_email_event(data, user_id, email_id):
    data[user_id]["events"].setdefault(email_id, {"status": PHISHING_EMAIL_STATUS[int(email_id)-1]})


def load_weekly_metrics():
    metrics = {}
    if not WEEKLY_METRICS_PATH.exists():
        return metrics
    
    with open(WEEKLY_METRICS_PATH, mode="r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metrics[row["email_id"]] = {
                "n_report": int(row["n_report"]),
                "n_no_report": int(row["n_no_report"]),
                "average_response_time": float(row["average_response_time"])
            }
    return metrics

def save_weekly_metrics(metrics):
    WEEKLY_METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(WEEKLY_METRICS_PATH, mode="w", newline="") as f:
        fieldnames = ["email_id", "n_report", "n_no_report", "average_response_time"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for email_id, data in metrics.items():
            writer.writerow({
                "email_id": email_id,
                "n_report": data["n_report"],
                "n_no_report": data["n_no_report"],
                "average_response_time": data["average_response_time"]
            })


def tracking_events(user_id: str, action: str, email_id: str):
    data = load_metrics()
    ensure_user(data, user_id)
    ensure_email_event(data, user_id, email_id)

    event_data = data[user_id]["events"][email_id]
    now = datetime.now(timezone.utc)

    # -------- EMAIL OPENED --------
    if action == A_EMAIL_OPENED:
        if A_EMAIL_OPENED not in event_data:
            event_data[A_EMAIL_OPENED] = now.isoformat()

    # -------- REPORT / NO_REPORT --------
    elif action in [A_REPORT, A_NO_REPORT]:
        if A_REPORT in event_data or A_NO_REPORT in event_data:
            return 

        if A_EMAIL_OPENED not in event_data:
            event_data[A_EMAIL_OPENED] = now.isoformat()

        opened_time = datetime.fromisoformat(event_data[A_EMAIL_OPENED])
        diff = (now - opened_time).total_seconds()

        event_data[action] = diff

        weekly_data = load_weekly_metrics()
        
        if email_id not in weekly_data:
            weekly_data[email_id] = {
                "n_report": 0,
                "n_no_report": 0,
                "average_response_time": 0.0
            }
        
        if action == A_REPORT:
            weekly_data[email_id]["n_report"] += 1
        elif action == A_NO_REPORT:
            weekly_data[email_id]["n_no_report"] += 1
            
        total_responses = weekly_data[email_id]["n_report"] + weekly_data[email_id]["n_no_report"]
        prev_avg = weekly_data[email_id]["average_response_time"]
        new_avg = prev_avg + ((diff - prev_avg) / total_responses)
        
        weekly_data[email_id]["average_response_time"] = new_avg
        
        save_weekly_metrics(weekly_data)

    else:
        raise ValueError(f"Unknown action: {action}")

    save_metrics(data)