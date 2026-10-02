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
