import os
import json
import requests
from dotenv import load_dotenv
import pandas as pd
from datetime import date

load_dotenv()
api_key = os.getenv("INSTANTLY_API_KEY")

url = "https://api.instantly.ai/api/v2/campaigns/analytics/daily"
headers = {"Authorization": f"Bearer {api_key}"}

params = {
    "campaign_id": "25acf12f-74a7-4699-a6c6-9ad10c668fc5",
    "start_date": "2026-07-01",
    "end_date": date.today().isoformat(),
}

response = requests.get(url, headers=headers, params=params)

print("Status code:", response.status_code)

data = response.json()

print(type(data))
print("Days returned:", len(data))

#print(json.dumps(data[0], indent=2))

df = pd.DataFrame(data)

print(df.shape)
print(df.head())

os.makedirs("data", exist_ok=True)

df.to_csv("data/daily_analytics.csv", index=False)