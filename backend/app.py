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
