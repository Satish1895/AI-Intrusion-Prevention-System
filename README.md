# 🛡️ Distributed AI Intrusion Prevention System (IPS)

This project features a **Distributed Architecture** designed to monitor network traffic across multiple devices using **MQTT** and **XGBoost**. It acts as a proactive security layer that not only detects threats but issues automated blocking commands.



## 📱 Two-Device Demo Setup
To demonstrate the "Distributed" nature of the system, you can use two separate devices on the same Wi-Fi network:

| Device | Role | Components Running |
| :--- | :--- | :--- |
| **Primary Laptop** | **Security Operations Center (SOC)** | MQTT Broker, `dashboard.py`, `detection_engine.py` |
| **Second Device** | **Remote Network Sensor** | `interactive_attacker.py` |

---

## 🚦 Execution Steps

### 1. Start the Central Hub (Primary Laptop)
Launch the backbone of the system on your main machine:
* **Start MQTT Broker:** Ensure Mosquitto or a similar broker is running on port 1883.
* **Run Dashboard:** `python dashboard.py`
* **Run AI Engine:** `python detection_engine.py`

> **Note:** The Dashboard is now live at `http://localhost:5000`. Because `host='0.0.0.0'` is used, it can also be accessed via your laptop's IP address (e.g., `http://192.168.1.XX:5000`).

### 2. Start the Remote Sensor (Second Device)
On your second device (or a separate terminal pointing to the Laptop's IP):
* **Update IP:** Change `BROKER = "127.0.0.1"` to your laptop's Local IP in `traffic_simulator.py`.
* **Run Simulation:** `python interactive_attacker.py`

### 3. Observe the Prevention Flow
1. **Detection:** As the simulator sends packets, the **XGBoost Engine** classifies them in real-time.
2. **Alerting:** Threat alerts are inserted into the `recent_alerts` list and emitted via **SocketIO**.
3. **Prevention:** When an attack is detected with **>80% confidence**, the engine publishes a `BLOCK` command to the `network/control` topic.
4. **Action:** The Dashboard listens for these control commands and updates the **"Active Blocking"** table instantly.

---

## 📊 Technical Highlights
* **Decoupled Communication:** The sensor and detection engine are fully decoupled, communicating only through MQTT topics like `network/traffic`.
* **Asynchronous Processing:** The dashboard uses a background thread (`mqtt_thread`) to listen for messages without freezing the web server.
* **Feature Rich Preprocessing:** Uses **SMOTE** to handle class imbalance and **MinMaxScaler** for data normalization before feeding it to the XGBoost model.
* **Active IPS Logic:** Moves beyond simple detection by implementing a feedback loop that triggers "BLOCK" commands based on model probability.



## 🛠️ Tech Stack
* **AI/ML:** XGBoost, Scikit-learn, SMOTE (Imbalanced-learn)
* **Communication:** Paho-MQTT, Flask-SocketIO
* **Backend:** Flask, Python Threading
* **Data:** Pandas, NumPy
