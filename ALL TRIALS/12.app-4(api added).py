from flask import Flask, request, jsonify, render_template
import sqlite3
import datetime
import joblib
import pandas as pd
import requests

app = Flask(__name__)

crop_model = joblib.load("crop_model.pkl")
fert_model = joblib.load("fert_model.pkl")
soil_enc = joblib.load("soil_encoder.pkl")
crop_type_enc = joblib.load("crop_type_encoder.pkl")

WEATHER_API_KEY = "f810c76000c66c1e15a693eebe482fcb"

def get_live_data():
    conn = sqlite3.connect("sensors.db")
    c = conn.cursor()
    c.execute("SELECT temperature, humidity FROM readings ORDER BY timestamp DESC LIMIT 1")
    latest = c.fetchone()
    conn.close()
    if latest:
        return latest[0], latest[1]
    return 25.0, 60.0

def get_api_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    try:
        res = requests.get(url).json()
        if res.get("cod") == 200:
            temp = res['main']['temp']
            hum = res['main']['humidity']
            rain = res.get('rain', {}).get('1h', 0.0) # mm of rain in last hour
            return temp, hum, rain
    except Exception as e:
        print("Weather API Error:", e)
    return None, None, None

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
    city = request.form.get('city', '').strip()
    
    if city:
        live_temp, live_hum, live_rain = get_api_weather(city)
        if live_temp is None: # Fallback if API fails
            live_temp, live_hum = get_live_data()
            live_rain = float(request.form['rainfall'])
    else:
        live_temp, live_hum = get_live_data()
        live_rain = float(request.form['rainfall'])
    
    input_df = pd.DataFrame([{
        'N': float(request.form['N']),
        'P': float(request.form['P']),
        'K': float(request.form['K']),
        'temperature': live_temp,
        'humidity': live_hum,
        'ph': float(request.form['ph']),
        'rainfall': live_rain
    }])
    
    prediction = crop_model.predict(input_df)[0]
    return render_template("index.html", live_temp=live_temp, live_hum=live_hum, crop_prediction=prediction, used_city=city)

@app.route("/predict_fert", methods=["POST"])
def predict_fert():
    city = request.form.get('city', '').strip()
    
    if city:
        live_temp, live_hum, _ = get_api_weather(city)
        if live_temp is None:
            live_temp, live_hum = get_live_data()
    else:
        live_temp, live_hum = get_live_data()
    
    soil_encoded = soil_enc.transform([request.form['soil_type']])[0]
    crop_encoded = crop_type_enc.transform([request.form['crop_type']])[0]
    
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
    return render_template("index.html", live_temp=live_temp, live_hum=live_hum, fert_prediction=prediction, used_city=city)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
