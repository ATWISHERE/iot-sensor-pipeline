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

12. new format app.py: 
from flask import Flask, request, jsonify
import sqlite3
import datetime
import joblib
import pandas as pd

app = Flask(__name__)

# 1. Load the Machine Learning Models (The "Frozen Brains")
crop_model = joblib.load("crop_model.pkl")
fert_model = joblib.load("fert_model.pkl")
soil_enc = joblib.load("soil_encoder.pkl")
crop_type_enc = joblib.load("crop_type_encoder.pkl")

# 2. Database Setup (The Memory)
def init_db():
    conn = sqlite3.connect("sensors.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS readings 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, temperature REAL, humidity REAL)''')
    conn.commit()
    conn.close()

init_db()

# 3. Hardware Route: Receives live sensor data and saves it permanently
@app.route("/sensor-data", methods=["POST"])
def receive_data():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    conn = sqlite3.connect("sensors.db")
    c = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO readings (timestamp, temperature, humidity) VALUES (?, ?, ?)",
              (timestamp, data.get("temperature"), data.get("humidity")))
    conn.commit()
    conn.close()
    
    print(f"Hardware saved live data: Temp={data.get('temperature')}C, Hum={data.get('humidity')}%")
    return jsonify({"status": "success"}), 200

# 4. AI Prediction Route: Merges manual user input with LIVE hardware data
@app.route("/predict_crop", methods=["POST"])
def predict_crop():
    manual_data = request.json
    
    # Pull the absolute latest temperature and humidity from our database
    conn = sqlite3.connect("sensors.db")
    c = conn.cursor()
    c.execute("SELECT temperature, humidity FROM readings ORDER BY timestamp DESC LIMIT 1")
    latest_reading = c.fetchone()
    conn.close()
    
    # Fallback just in case the hardware hasn't sent anything yet
    if latest_reading:
        live_temp, live_hum = latest_reading
    else:
        live_temp, live_hum = 25.0, 60.0 # Default fallback values
        
    # Package exactly what the model expects, mixing manual input with live sensor data
    input_df = pd.DataFrame([{
        'N': manual_data['N'],
        'P': manual_data['P'],
        'K': manual_data['K'],
        'temperature': live_temp,  # USING LIVE HARDWARE DATA
        'humidity': live_hum,      # USING LIVE HARDWARE DATA
        'ph': manual_data['ph'],
        'rainfall': manual_data['rainfall']
    }])
    
    # Ask the loaded AI model for a prediction
    prediction = crop_model.predict(input_df)
    
    return jsonify({
        "live_temperature_used": live_temp,
        "live_humidity_used": live_hum,
        "recommended_crop": prediction[0]
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)



13.working :fix that 404 Not Found error in your browser by building the "Face" of your app—a clean web dashboard.

Flask requires HTML files to live inside a specific folder named templates.
		mkdir templates

		notepad templates\index.html
<!DOCTYPE html>
<html>
<head>
    <title>Smart Farm AI</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px; }
        .card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 450px; margin: auto; }
        input, button { width: 100%; padding: 10px; margin-top: 8px; margin-bottom: 15px; box-sizing: border-box; border-radius: 5px; border: 1px solid #ccc; }
        button { background-color: #28a745; color: white; border: none; cursor: pointer; font-weight: bold; font-size: 16px; }
        button:hover { background-color: #218838; }
        .live-data { background-color: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="card">
        <h2 style="text-align: center; color: #333;">?? Crop Recommender</h2>
        
        <!-- Live hardware data gets injected here automatically -->
        <div class="live-data">
            <p style="margin: 5px 0;">?? <b>Live Temp:</b> {{ live_temp }} &deg;C</p>
            <p style="margin: 5px 0;">?? <b>Live Hum:</b> {{ live_hum }} %</p>
        </div>

        <form action="/predict_crop" method="POST">
            <label>Nitrogen (N):</label> <input type="number" name="N" required>
            <label>Phosphorus (P):</label> <input type="number" name="P" required>
            <label>Potassium (K):</label> <input type="number" name="K" required>
            <label>pH Level:</label> <input type="number" step="0.1" name="ph" required>
            <label>Rainfall (mm):</label> <input type="number" name="rainfall" required>
            <button type="submit">Predict Best Crop</button>
        </form>

        <!-- The AI Prediction will appear here after clicking predict -->
        {% if prediction %}
            <h3 style="color: #28a745; text-align: center; border-top: 2px solid #28a745; padding-top: 15px;">
                Recommended: {{ prediction | upper }}
            </h3>
        {% endif %}
    </div>
</body>
</html>		



14.Connect the Backend to the Webpage:we need to tell app.py to display this HTML file instead of looking for hidden JSON payloads. Run notepad app.py and replace your code with this finalized version.

Note: The only changes here are using render_template to show the HTML, and request.form to read data from the text boxes.

from flask import Flask, request, jsonify, render_template
import sqlite3
import datetime
import joblib
import pandas as pd

app = Flask(__name__)

# Load Models
crop_model = joblib.load("crop_model.pkl")
fert_model = joblib.load("fert_model.pkl")
soil_enc = joblib.load("soil_encoder.pkl")
crop_type_enc = joblib.load("crop_type_encoder.pkl")

# Helper function to grab the live database numbers
def get_live_data():
    conn = sqlite3.connect("sensors.db")
    c = conn.cursor()
    c.execute("SELECT temperature, humidity FROM readings ORDER BY timestamp DESC LIMIT 1")
    latest = c.fetchone()
    conn.close()
    if latest:
        return latest[0], latest[1]
    return 25.0, 60.0 # Fallback if no hardware data exists yet

# Visibe Web Homepage
@app.route("/", methods=["GET"])
def dashboard():
    live_temp, live_hum = get_live_data()
    return render_template("index.html", live_temp=live_temp, live_hum=live_hum)

# Hidden Hardware Door
@app.route("/sensor-data", methods=["POST"])
def receive_data():
    data = request.get_json(silent=True)
    conn = sqlite3.connect("sensors.db")
    c = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO readings (timestamp, temperature, humidity) VALUES (?, ?, ?)",
              (timestamp, data.get("temperature"), data.get("humidity")))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"}), 200

# Web Form Processing
@app.route("/predict_crop", methods=["POST"])
def predict_crop():
    live_temp, live_hum = get_live_data()
    
    # Read the numbers the user typed into the web form
    input_df = pd.DataFrame([{
        'N': float(request.form['N']),
        'P': float(request.form['P']),
        'K': float(request.form['K']),
        'temperature': live_temp,
        'humidity': live_hum,
        'ph': float(request.form['ph']),
        'rainfall': float(request.form['rainfall'])
    }])
    
    prediction = crop_model.predict(input_df)[0]
    
    # Reload the page with the answer displayed
    return render_template("index.html", live_temp=live_temp, live_hum=live_hum, prediction=prediction)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


	