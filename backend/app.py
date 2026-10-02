from flask import Flask, request, jsonify, render_template
import sqlite3
import datetime
import joblib
import pandas as pd
import requests

app = Flask(__name__)

# Load Models and Encoders
crop_model = joblib.load("crop_model.pkl")
fert_model = joblib.load("fert_model.pkl")
soil_enc = joblib.load("soil_encoder.pkl")
crop_type_enc = joblib.load("crop_type_encoder.pkl")

WEATHER_API_KEY = "f810c76000c66c1e15a693eebe482fcb"

def get_live_hardware_data():
    conn = sqlite3.connect("sensors.db")
    c = conn.cursor()
    c.execute("SELECT temperature, humidity FROM readings ORDER BY timestamp DESC LIMIT 1")
    latest = c.fetchone()
    conn.close()
    if latest:
        return latest[0], latest[1]
    return 25.5, 60.0

def get_api_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    try:
        res = requests.get(url, timeout=5).json()
        if res.get("cod") == 200:
            temp = round(res['main']['temp'], 1)
            hum = round(res['main']['humidity'], 1)
            rain = round(res.get('rain', {}).get('1h', 0.0), 1)
            return temp, hum, rain
    except Exception as e:
        print("Weather API Exception:", e)
    return None, None, None

# 1. Main Dashboard View
@app.route("/", methods=["GET"])
def dashboard():
    hw_temp, hw_hum = get_live_hardware_data()
    return render_template("index.html", hw_temp=hw_temp, hw_hum=hw_hum)

# 2. Asynchronous API for Frontend Auto-Fill
@app.route("/api/weather", methods=["GET"])
def api_weather_lookup():
    city = request.args.get("city", "").strip()
    if not city:
        return jsonify({"success": False, "error": "City name is empty"}), 400
    
    temp, hum, rain = get_api_weather(city)
    if temp is None:
        return jsonify({"success": False, "error": f"City '{city}' not found or API key still activating."}), 404
        
    return jsonify({
        "success": True,
        "city": city,
        "temperature": temp,
        "humidity": hum,
        "rainfall": rain
    }), 200

# 3. Microcontroller Data Endpoint
@app.route("/sensor-data", methods=["POST"])
def receive_sensor_data():
    data = request.get_json(silent=True)
    if not data or "temperature" not in data or "humidity" not in data:
        return jsonify({"error": "Invalid payload"}), 400
        
    conn = sqlite3.connect("sensors.db")
    c = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO readings (timestamp, temperature, humidity) VALUES (?, ?, ?)",
              (timestamp, data["temperature"], data["humidity"]))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"}), 200

# 4. Crop Prediction Endpoint
@app.route("/predict_crop", methods=["POST"])
def predict_crop():
    hw_temp, hw_hum = get_live_hardware_data()
    
    # Read form inputs (falls back to hardware values if left blank)
    temp = float(request.form.get("temp") or hw_temp)
    hum = float(request.form.get("hum") or hw_hum)
    rain = float(request.form.get("rainfall") or 100.0)
    n = float(request.form.get("N", 0))
    p = float(request.form.get("P", 0))
    k = float(request.form.get("K", 0))
    ph = float(request.form.get("ph", 6.5))
    
    input_df = pd.DataFrame([{
        'N': n, 'P': p, 'K': k,
        'temperature': temp,
        'humidity': hum,
        'ph': ph,
        'rainfall': rain
    }])
    
    pred = crop_model.predict(input_df)[0]
    return render_template("index.html", 
                           hw_temp=hw_temp, 
                           hw_hum=hw_hum, 
                           crop_prediction=pred, 
                           used_crop_city=request.form.get("city", ""))

# 5. Fertilizer Prediction Endpoint
@app.route("/predict_fert", methods=["POST"])
def predict_fert():
    hw_temp, hw_hum = get_live_hardware_data()
    
    temp = float(request.form.get("temp") or hw_temp)
    hum = float(request.form.get("hum") or hw_hum)
    moist = float(request.form.get("moisture", 30))
    n = float(request.form.get("N", 0))
    k = float(request.form.get("K", 0))
    p = float(request.form.get("P", 0))
    
    soil_encoded = soil_enc.transform([request.form['soil_type']])[0]
    crop_encoded = crop_type_enc.transform([request.form['crop_type']])[0]
    
    input_df = pd.DataFrame([{
        'Temparature': temp,
        'Humidity ': hum,
        'Moisture': moist,
        'Soil Type': soil_encoded,
        'Crop Type': crop_encoded,
        'Nitrogen': n,
        'Potassium': k,
        'Phosphorous': p
    }])
    
    pred = fert_model.predict(input_df)[0]
    return render_template("index.html", 
                           hw_temp=hw_temp, 
                           hw_hum=hw_hum, 
                           fert_prediction=pred,
                           used_fert_city=request.form.get("city", ""))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
