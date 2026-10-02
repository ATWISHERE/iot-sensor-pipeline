# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import sqlite3
import datetime

app = Flask(__name__)

# 1. Create a database to store the readings permanently
def init_db():
    conn = sqlite3.connect('sensors.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS readings
                 (id INTEGER PRIMARY KEY, timestamp TEXT, temperature REAL, humidity REAL)''')
    conn.commit()
    conn.close()

init_db()

# 2. The endpoint where hardware will send data
@app.route('/sensor-data', methods=['POST'])
def receive_data():
    data = request.json
    print(f"Data received: {data}")
    
    conn = sqlite3.connect('sensors.db')
    c = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute("INSERT INTO readings (timestamp, temperature, humidity) VALUES (?, ?, ?)",
              (timestamp, data.get('temperature'), data.get('humidity')))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success"}), 200

# 3. A visible dashboard route for your web browser
@app.route('/', methods=['GET'])
def dashboard():
    conn = sqlite3.connect('sensors.db')
    c = conn.cursor()
    c.execute("SELECT * FROM readings ORDER BY timestamp DESC LIMIT 5")
    rows = c.fetchall()
    conn.close()
    
    # Very simple HTML to show the data in your browser
    html = "<h1>Live Sensor Dashboard</h1><ul>"
    for row in rows:
        html += f"<li>{row[1]} - Temp: {row[2]}&deg;C, Humidity: {row[3]}%</li>"
    html += "</ul>"
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)