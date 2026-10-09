import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("INSTANTLY_API_KEY")

if api_key:
    print("Key loaded. Starts with:", api_key[:4])
else:
    print("Key NOT found. Check the .env file.")