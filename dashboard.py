from flask import Flask, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json
import threading

# --- Flask and SocketIO Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
# cors_allowed_origins="*" ensures your phone can connect to the dashboard UI
socketio = SocketIO(app, cors_allowed_origins="*")

# --- MQTT Configuration ---
# Since the Dashboard runs on the SAME laptop as the Broker, we use localhost.
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "dashboard_listener_v3"

# --- TOPICS (CRITICAL UPDATE) ---
# We must subscribe to 'network/control' to hear the IPS block commands!
TOPICS = [
    ("network/alerts", 0), 
    ("network/stats", 0),
    ("network/control", 0) # <--- THIS WAS MISSING BEFORE
]

# --- Global Data Storage ---
stats = {'total': 0, 'normal': 0, 'attacks': 0, 'dos': 0, 'probe': 0, 'r2l': 0, 'u2r': 0}
recent_alerts = []
blocked_devices = [] # Stores list of blocked IPs

# --- Paho-MQTT Functions ---

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the broker."""
    if rc == 0:
        print("✅ Dashboard: Connected to MQTT broker")
        client.subscribe(TOPICS)
    else:
        print(f"❌ Dashboard: Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    """Callback for when a message is received."""
    global stats, recent_alerts, blocked_devices
    
    try:
        payload = json.loads(msg.payload.decode())

        # 1. Update Statistics
        if msg.topic == 'network/stats':
            stats = payload
            socketio.emit('update_stats', stats)
            
        # 2. Handle New Threat Alerts
        elif msg.topic == 'network/alerts':
            recent_alerts.insert(0, payload)
            if len(recent_alerts) > 50:
                recent_alerts.pop()
            socketio.emit('new_alert', payload)

        # 3. Handle IPS Block Commands (The Fix!)
        elif msg.topic == 'network/control':
            # Only process if it's a BLOCK command
            if payload.get('command') == 'BLOCK':
                blocked_devices.insert(0, payload)
                if len(blocked_devices) > 20:
                    blocked_devices.pop()
                
                print(f"🚫 DASHBOARD: Received Block Command for {payload.get('target')}")
                # Emit event to the HTML frontend to update the table
                socketio.emit('new_block', payload)
            
    except Exception as e:
        print(f"Error processing message from topic {msg.topic}: {e}")

def start_mqtt_client():
    """Starts the Paho-MQTT client in a background thread."""
    client = mqtt.Client(client_id=MQTT_CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"Error connecting Paho client: {e}")

# --- Flask Routes ---

@app.route('/')
def index():
    """Serve the main dashboard page."""
    # Pass all data so the page isn't empty on reload
    return render_template('dashboard.html', 
                           stats=stats, 
                           alerts=recent_alerts, 
                           blocked=blocked_devices)

# --- Main Execution ---

if __name__ == '__main__':
    # Start the MQTT listener in a separate thread
    mqtt_thread = threading.Thread(target=start_mqtt_client)
    mqtt_thread.daemon = True 
    mqtt_thread.start()
    
    # Start the Web Server
    # host='0.0.0.0' allows you to see the dashboard on your Phone/Laptop B
    print("Starting Flask-SocketIO server at http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)