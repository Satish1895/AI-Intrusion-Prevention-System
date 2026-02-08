import paho.mqtt.client as mqtt
import json
import pandas as pd
import joblib
from datetime import datetime
import csv
import threading
import time

# --- Load Trained AI Models ---
try:
    print("Loading AI model (XGBoost)...")
    
    # 1. Load the XGBoost Model
    model = joblib.load('models/xgboost_model.pkl') 
    
    # 2. Load the Label Encoder (CRITICAL for XGBoost)
    # XGBoost outputs numbers (0, 1, 2), this converts them back to names ('Normal', 'DoS')
    le = joblib.load('models/label_encoder.pkl')
    
    # 3. Load Preprocessing Tools
    scaler = joblib.load('scaler.pkl')
    selected_features = joblib.load('models/selected_features.pkl')
    feature_names = joblib.load('feature_names.pkl')
    
    print("✅ XGBoost Engine loaded successfully.")
except FileNotFoundError as e:
    print(f"❌ Error loading model files: {e}")
    print("Make sure you ran the XGBoost training script and saved 'label_encoder.pkl'!")
    exit()

# --- MQTT Configuration ---
BROKER = "127.0.0.1" 
PORT = 1883

# Topics
SUBSCRIBE_TOPIC = "network/traffic"
ALERT_TOPIC = "network/alerts"
STATS_TOPIC = "network/stats"
CONTROL_TOPIC = "network/control"

# Metrics tracking
detection_stats = {
    'total': 0, 'normal': 0, 'attacks': 0, 
    'dos': 0, 'probe': 0, 'r2l': 0, 'u2r': 0
}

def publish_stats(client):
    """Background thread to publish stats every 1 second"""
    while True:
        try:
            client.publish(STATS_TOPIC, json.dumps(detection_stats))
        except Exception as e:
            print(f"Error publishing stats: {e}")
        time.sleep(1)

def preprocess_message(data):
    """Preprocess a single JSON packet for the AI model"""
    # 1. Convert to DataFrame
    df = pd.DataFrame([data])
    
    # 2. Drop non-feature columns
    if 'label' in df.columns: df = df.drop('label', axis=1)
    if 'source_ip' in df.columns: df = df.drop('source_ip', axis=1)
    
    # 3. One-hot encode
    categorical = ['protocol_type', 'service', 'flag']
    df_encoded = pd.get_dummies(df, columns=categorical)
    
    # 4. Align columns
    df_aligned = df_encoded.reindex(columns=feature_names, fill_value=0)
    
    # 5. Scale
    df_scaled = scaler.transform(df_aligned)
    df_scaled = pd.DataFrame(df_scaled, columns=feature_names)
    
    # 6. Select Features
    df_selected = df_scaled[selected_features]
    
    return df_selected

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with code: {rc}")
    client.subscribe(SUBSCRIBE_TOPIC)

def on_message(client, userdata, msg):
    try:
        # Parse incoming message
        data = json.loads(msg.payload.decode())
        
        # Preprocess
        features = preprocess_message(data)
        
        # --- XGBOOST PREDICTION LOGIC ---
        # 1. Predict (Returns an integer index, e.g., 0, 1, 3)
        pred_index = model.predict(features)[0]
        
        # 2. Decode (Converts index to string, e.g., 1 -> 'DoS')
        prediction = le.inverse_transform([pred_index])[0]
        
        # 3. Get Confidence (Max probability)
        probability = model.predict_proba(features).max()
        
        # --- Update Stats & Alerts ---
        detection_stats['total'] += 1
        
        if prediction == 'Normal':
            detection_stats['normal'] += 1
        else:
            detection_stats['attacks'] += 1
            pred_key = prediction.lower()
            if pred_key in detection_stats:
                detection_stats[pred_key] += 1
            
            # Generate Alert
            alert = {
                'timestamp': datetime.now().isoformat(),
                'attack_type': prediction,
                'confidence': float(probability),
                'source': data.get('protocol_type', 'unknown'),
                'severity': 'HIGH' if prediction in ['DoS', 'U2R'] else 'MEDIUM',
                'source_ip': data.get('source_ip', 'Unknown')
            }
            
            client.publish(ALERT_TOPIC, json.dumps(alert))
            
            # IPS Block Logic (> 80% confidence)
            if probability > 0.80:
                block_cmd = {
                    'command': 'BLOCK',
                    'target': data.get('source_ip', 'unknown'),
                    'reason': f"{prediction} Attack Detected",
                    'timestamp': datetime.now().isoformat()
                }
                client.publish(CONTROL_TOPIC, json.dumps(block_cmd))
                print(f"🛑 IPS BLOCK: {data.get('source_ip')} ({prediction})")

            print(f"ALERT: {prediction} detected")

    except Exception as e:
        print(f"Error processing message: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    client = mqtt.Client("DetectionEngine")
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER, PORT, 60)
    except Exception as e:
        print(f"Could not connect to MQTT broker: {e}")
        exit()

    print("🚀 XGBoost Detection Engine Started...")
    
    stats_thread = threading.Thread(target=publish_stats, args=(client,))
    stats_thread.daemon = True
    stats_thread.start()

    client.loop_forever()