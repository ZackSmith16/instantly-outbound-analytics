import os
import requests
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
api_key = os.getenv("INSTANTLY_API_KEY")

url = "https://api.instantly.ai/api/v2/leads/list"
headers = {"Authorization": f"Bearer {api_key}"}

all_leads = [] # Empty list to collect every lead
starting_after = None # No bookmark yet for the first page

while True:
    body = {
        "campaign": "25acf12f-74a7-4699-a6c6-9ad10c668fc5",
        "limit": 100,
}
    if starting_after:
        body["starting_after"] = starting_after
    response = requests.post(url, headers=headers, json=body)
    data = response.json()

    all_leads.extend(data["items"])
    print("Leads collected so far:", len(all_leads))

    starting_after = data.get("next_starting_after")
    if not starting_after:
        break

df = pd.DataFrame(all_leads)
print(df.shape)

os.makedirs("data", exist_ok=True)
df.to_csv("data/leads.csv", index=False)
