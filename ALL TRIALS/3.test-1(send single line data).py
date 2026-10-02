import urllib.request
import json

url = "http://127.0.0.1:5000/sensor-data"
# The simulated sensor data
data = json.dumps({"temperature": 25.5, "humidity": 60.0}).encode("utf-8")
headers = {"Content-Type": "application/json"}

try:
    req = urllib.request.Request(url, data=data, headers=headers)
    response = urllib.request.urlopen(req)
    print("Server Response:", response.read().decode())
except Exception as e:
    print("Failed to send data:", e)