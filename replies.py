import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("INSTANTLY_API_KEY")

url = "https://api.instantly.ai/api/v2/emails"
headers = {"Authorization": f"Bearer {api_key}"}

all_emails = []
starting_after = None

while True:
    params = {
        "campaign_id": "25acf12f-74a7-4699-a6c6-9ad10c668fc5",
        "email_type": "received",
        "limit": 100,
    }
    if starting_after:
        params["starting_after"] = starting_after

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()   # crash loudly on 401/429 instead of continuing
    data = response.json()

    all_emails.extend(data["items"])
    print("Replies collected so far:", len(all_emails))

    starting_after = data.get("next_starting_after")
    if not starting_after or not data["items"]:
        break
    time.sleep(3)   # this endpoint only allows 20 requests per minute

rows = []
for e in all_emails:
    rows.append({
        "email_id": e.get("id"),
        "timestamp_email": e.get("timestamp_email"),
        "lead_email": e.get("lead"),
        "step": e.get("step"),
        "is_auto_reply": e.get("is_auto_reply"),
        "i_status": e.get("i_status"),
        "ai_interest_value": e.get("ai_interest_value"),
        "subject": e.get("subject"),
        "body_text": (e.get("body") or {}).get("text"),
    })

df = pd.DataFrame(rows)
print(df.shape)
print(df[["timestamp_email", "step", "is_auto_reply"]])

os.makedirs("data", exist_ok=True)
df.to_csv("data/replies.csv", index=False)

