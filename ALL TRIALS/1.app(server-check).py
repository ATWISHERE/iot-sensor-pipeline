from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/sensor-data', methods=['POST'])
def receive_data():
    # Receive JSON data from the hardware
    data = request.json
    
    # Print it to the console (later we will save this to a database)
    print(f"Live Sensor Data: {data}")
    
    return jsonify({"status": "success", "message": "Data received!"}), 200

if __name__ == '__main__':
    # host='0.0.0.0' allows devices on your local network to send data to this PC
    app.run(host='0.0.0.0', port=5000)