import requests

url = "https://maestro-ai.up.railway.app/live/session"  # Update if needed

for i in range(20):
    response = requests.get(url)
    print(f"Request {i+1}: Status {response.status_code}")
    if response.status_code == 429:
        print("Rate limit hit:", response.text)
        break
    else:
        print("Response:", response.text[:100])  # Print first 100 chars