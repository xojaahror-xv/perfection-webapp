import urllib.request
import json

url = "https://perfection-webapp.onrender.com/api/check_writing"
data = json.dumps({"text": "Hello this is a test essay to see if it works or fails.", "task_type": "General"}).encode("utf-8")
headers = {"Content-Type": "application/json"}
req = urllib.request.Request(url, data=data, headers=headers)

try:
    with urllib.request.urlopen(req) as response:
        print("Status:", response.status)
        print("Response:", response.read().decode("utf-8"))
except Exception as e:
    print("Error:", e)
