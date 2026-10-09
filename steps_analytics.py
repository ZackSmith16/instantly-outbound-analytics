import os
import json
import requests
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
api_key = os.getenv("INSTANTLY_API_KEY")

url = "https://api.instantly.ai/api/v2/campaigns/analytics/steps"
headers = {"Authorization": f"Bearer {api_key}"}

params = {
    "campaign_id": "25acf12f-74a7-4699-a6c6-9ad10c668fc5"
}

response = requests.get(url, headers=headers, params=params)

print("Status code:", response.status_code)

data = response.json()

print(type(data))


#print(json.dumps(data[0], indent=2))

df = pd.DataFrame(data)

print(df.shape)

df["reply_rate"] = (df["unique_replies"] / df["sent"]) * 100


df = df.dropna(subset=["step"])
df = df.sort_values(["step", "variant"])

print(df[["step", "variant", "sent", "unique_replies", "reply_rate"]])

os.makedirs("data", exist_ok=True)

df.to_csv("data/steps_analytics.csv", index=False)
