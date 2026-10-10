import os
import json
from datetime import datetime, timezone

import functions_framework
from google.cloud import bigquery

client = bigquery.Client()
TABLE_ID = "instantly-outbound-analytics.instantly_raw.webhook_events"


@functions_framework.http
def receive_event(request):
    sent_secret = request.headers.get("X-Webhook-Secret")
    if sent_secret != os.environ.get("WEBHOOK_SECRET"):
        return ("Unauthorized", 401)

    event = request.get_json(silent=True)
    if event is None:
        return ("Bad request: expected JSON", 400)

    row = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "event_type": event.get("event_type"),
        "campaign_id": event.get("campaign_id"),
        "lead_email": event.get("lead_email"),
        "payload": json.dumps(event),
    }
    errors = client.insert_rows_json(TABLE_ID, [row])
    if errors:
        print("BigQuery insert failed:", errors)
        return ("Insert failed", 500)  

    return ("OK", 200)