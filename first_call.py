import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("INSTANTLY_API_KEY")

url = "https://api.instantly.ai/api/v2/campaigns"
headers = {"Authorization": f"Bearer {api_key}"}

response = requests.get(url, headers=headers)

print("Status code:", response.status_code)

data = response.json()
print(data.keys())

campaigns = data["items"]

print("Number of campaigns:", len(campaigns))

for c in campaigns:
    print(c["name"])