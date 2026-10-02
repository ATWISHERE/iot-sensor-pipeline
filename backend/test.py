import urllib.request
import json

url = "http://127.0.0.1:5000/predict_crop"

# Simulating manual data (N, P, K, pH, Rainfall). 
# Temp and Humidity are NOT here because the server pulls them live from the database!
data = json.dumps({
    "N": 90, 
    "P": 42, 
    "K": 43, 
    "ph": 6.5, 
    "rainfall": 200
}).encode("utf-8")

headers = {"Content-Type": "application/json"}

try:
    req = urllib.request.Request(url, data=data, headers=headers)
    response = urllib.request.urlopen(req)
    print("AI Server Prediction:", response.read().decode())
except Exception as e:
    print("Failed to get prediction:", e)

