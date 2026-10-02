import datetime
import sqlite3
from flask import Flask, jsonify, request

app = Flask(__name__)


# 1. Create a database to store the readings permanently
def init_db():
  conn = sqlite3.connect("sensors.db")
  c = conn.cursor()
  c.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            temperature REAL,
            humidity REAL
        )
    """)
  conn.commit()
  conn.close()


init_db()


# 2. The endpoint where hardware will send data
@app.route("/sensor-data", methods=["POST"])
def receive_data():
  # Ensure JSON data is parsed safely
  data = request.get_json(silent=True)
  if not data:
    return (
        jsonify({
            "error": "Invalid or missing JSON payload. Ensure Content-Type is application/json."
        }),
        400,
    )

  print(f"Data received: {data}")

  temperature = data.get("temperature")
  humidity = data.get("humidity")

  conn = sqlite3.connect("sensors.db")
  c = conn.cursor()
  timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  c.execute(
      "INSERT INTO readings (timestamp, temperature, humidity) VALUES (?, ?,"
      " ?)",
      (timestamp, temperature, humidity),
  )
  conn.commit()
  conn.close()

  return jsonify({"status": "success"}), 200


# 3. A visible dashboard route for your web browser
@app.route("/", methods=["GET"])
def dashboard():
  conn = sqlite3.connect("sensors.db")
  c = conn.cursor()
  c.execute("SELECT id, timestamp, temperature, humidity FROM readings ORDER BY timestamp DESC LIMIT 5")
  rows = c.fetchall()
  conn.close()

  html = "<h1>Live Sensor Dashboard</h1><ul>"
  for row in rows:
    # row = (id, timestamp, temperature, humidity)
    html += f"<li>{row[1]} — Temp: {row[2]}°C, Humidity: {row[3]}%</li>"
  html += "</ul>"
  return html


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)
