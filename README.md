# 🛡️ Distributed AI Intrusion Prevention System (IPS)

This project is a real-time network security solution that utilizes **XGBoost** machine learning to detect and automatically mitigate cyber threats. It features a distributed microservices architecture using **MQTT** for communication and a live **Flask-SocketIO** dashboard for visualization.



## 🛠️ Requirements & Installation

### 1. Prerequisites
* **Python 3.8+**
* **MQTT Broker:** You must have an MQTT broker installed and running.
    * *Recommended:* **Eclipse Mosquitto**.
    * **Windows:** Download the installer from the official Mosquitto website.
    * **Linux:** `sudo apt install mosquitto mosquitto-clients`.

### 2. Setup & Installation
```bash
# Clone the repository
git clone [https://github.com/Satish1895/AI-Intrusion-Prevention-System.git](https://github.com/Satish1895/AI-Intrusion-Prevention-System.git)
cd AI-Intrusion-Prevention-System

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt 
```

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
