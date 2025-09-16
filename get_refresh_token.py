import requests
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
CODE = os.getenv("CODE")


res = requests.post(
    "https://www.strava.com/oauth/token",
    data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': CODE,
        'grant_type': 'authorization_code'
    }
)

print("Response JSON:")
print(res.json())
