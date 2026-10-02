from flask import Flask, request, jsonify, render_template
import sqlite3
import datetime
import joblib
import pandas as pd

app = Flask(__name__)

# Load Models and Translators
crop_model = joblib.load("crop_model.pkl")
fert_model = joblib.load("fert_model.pkl")
soil_enc = joblib.load("soil_encoder.pkl")
crop_type_enc = joblib.load("crop_type_encoder.pkl")

# Helper function for live data
def get_live_data():
    conn = sqlite3.connect("sensors.db")
    c = conn.cursor()
    c.execute("SELECT temperature, humidity FROM readings ORDER BY timestamp DESC LIMIT 1")
    latest = c.fetchone()
    conn.close()
    if latest:
        return latest[0], latest[1]
    return 25.0, 60.0

@app.route("/", methods=["GET"])
def dashboard():
    live_temp, live_hum = get_live_data()
    return render_template("index.html", live_temp=live_temp, live_hum=live_hum)

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

@app.route("/predict_crop", methods=["POST"])
def predict_crop():
    live_temp, live_hum = get_live_data()
    
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
    return render_template("index.html", live_temp=live_temp, live_hum=live_hum, crop_prediction=prediction)

@app.route("/predict_fert", methods=["POST"])
def predict_fert():
    live_temp, live_hum = get_live_data()
    
    # Translate strings from dropdown menu into numbers for the AI
    soil_encoded = soil_enc.transform([request.form['soil_type']])[0]
    crop_encoded = crop_type_enc.transform([request.form['crop_type']])[0]
    
    # Column names must match the original dataset perfectly
    input_df = pd.DataFrame([{
        'Temparature': live_temp,
        'Humidity ': live_hum,
        'Moisture': float(request.form['moisture']),
        'Soil Type': soil_encoded,
        'Crop Type': crop_encoded,
        'Nitrogen': float(request.form['N']),
        'Potassium': float(request.form['K']),
        'Phosphorous': float(request.form['P'])
    }])
    
    prediction = fert_model.predict(input_df)[0]
    return render_template("index.html", live_temp=live_temp, live_hum=live_hum, fert_prediction=prediction)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
