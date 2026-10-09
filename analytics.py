import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("INSTANTLY_API_KEY")

url = "https://api.instantly.ai/api/v2/campaigns/analytics"
headers = {"Authorization": f"Bearer {api_key}"}

response = requests.get(url, headers=headers)

print("Status code:", response.status_code)

data = response.json()

print(type(data))

#print(json.dumps(data, indent=2))

campaign = data[0]

reply_rate = round((campaign["reply_count"] / campaign["new_leads_contacted_count"]) * 100, 1)
bounce_rate = round((campaign["bounced_count"] / campaign["new_leads_contacted_count"]) * 100, 1)

print(f"Reply rate: {reply_rate}%")
print(f"Bounce rate: {bounce_rate}%")

print("Real replies:", campaign["reply_count"])
print("Auto replies:", campaign["reply_count_automatic"])