import paho.mqtt.client as mqtt
import json
import time
import random
import sys
import threading

# --- CONFIGURATION ---
# Use the Laptop IP you found earlier
BROKER = "10.63.11.219" 
PORT = 1883

TOPIC = "network/traffic"
CONTROL_TOPIC = "network/control"
MY_IP = "10.10.10.50" 
BLOCKED = False

# FIX FOR PAHO 2.0+
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "Live_Attacker_Device")

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"✅ Connected to Server at {BROKER}")
        client.subscribe(CONTROL_TOPIC)
    else:
        print(f"❌ Connection Failed (Code: {rc})")

def on_message(client, userdata, msg):
    global BLOCKED
    try:
        payload = json.loads(msg.payload.decode())
        if payload.get('command') == 'BLOCK' and payload.get('target') == MY_IP:
            BLOCKED = True
            print(f"\n🚫 BLOCKED BY FIREWALL: {payload.get('reason')}")
    except: pass

client.on_connect = on_connect
client.on_message = on_message

# --- PACKET GENERATORS ---

base_packet = {
    "duration":0,"protocol_type":"tcp","service":"http","flag":"SF",
    "src_bytes":100,"dst_bytes":0,"land":0,"wrong_fragment":0,"urgent":0,
    "hot":0,"num_failed_logins":0,"logged_in":1,"num_compromised":0,
    "root_shell":0,"su_attempted":0,"num_root":0,"num_file_creations":0,
    "num_shells":0,"num_access_files":0,"num_outbound_cmds":0,"is_host_login":0,
    "is_guest_login":0,"count":1,"srv_count":1,"serror_rate":0.0,
    "srv_serror_rate":0.0,"rerror_rate":0.0,"srv_rerror_rate":0.0,
    "same_srv_rate":1.0,"diff_srv_rate":0.0,"srv_diff_host_rate":0.0,
    "dst_host_count":1,"dst_host_srv_count":1,"dst_host_same_srv_rate":1.0,
    "dst_host_diff_srv_rate":0.0,"dst_host_same_src_port_rate":0.0,
    "dst_host_srv_diff_host_rate":0.0,"dst_host_serror_rate":0.0,
    "dst_host_srv_serror_rate":0.0,"dst_host_rerror_rate":0.0,
    "dst_host_srv_rerror_rate":0.0,"source_ip":MY_IP
}

def generate_normal():
    """Generates a random Normal HTTP packet (Safe Traffic)"""
    pkt = base_packet.copy()
    pkt.update({
        'protocol_type': 'tcp', 'service': 'http', 'flag': 'SF',
        'src_bytes': random.randint(200, 1500), # Realistic size
        'dst_bytes': random.randint(200, 8000),
        'duration': random.randint(0, 2),
        'count': random.randint(1, 10),
        'logged_in': 1, 
        'root_shell': 0
    })
    return pkt

def generate_dos():
    """Neptune DoS"""
    pkt = base_packet.copy()
    pkt.update({
        'protocol_type': 'tcp', 'service': 'private', 'flag': 'S0',
        'src_bytes': 0, 'dst_bytes': 0, 'count': 250, 'srv_count': 250,
        'serror_rate': 1.0, 'dst_host_serror_rate': 1.0, 'logged_in': 0
    })
    return pkt

def generate_probe():
    """Satan Probe"""
    pkt = base_packet.copy()
    pkt.update({
        'protocol_type': 'tcp', 'service': 'other', 'flag': 'SF',
        'src_bytes': 1, 'dst_bytes': 1,
        'duration': random.randint(1, 5),
        'count': random.randint(1, 5), 
        'same_srv_rate': 0.01,
        'dst_host_diff_srv_rate': 0.8,
        'dst_host_count': 255
    })
    return pkt

def generate_r2l():
    """Multi-Vector R2L: Tries 'Phf' (Web Exploit) or 'Spy' (Monitoring)"""
    pkt = base_packet.copy()
    
    # Randomly choose between two distinct R2L signatures
    attack_subtype = random.choice(['phf', 'spy'])
    
    if attack_subtype == 'phf':
        # TYPE 1: The "Phf" Attack (Web Server Exploit)
        pkt.update({
            'protocol_type': 'tcp',
            'service': 'http',       
            'flag': 'SF',            
            'src_bytes': 51,         
            'dst_bytes': 1000,       
            'hot': 3,                
            'num_compromised': 1,    
            'root_shell': 0,         
            'is_guest_login': 0,
            'count': 1
        })
    else:
        # TYPE 2: The "Spy" Attack (Session Hijack/Monitoring)
        pkt.update({
            'protocol_type': 'tcp',
            'service': 'telnet',
            'flag': 'RSTR',          
            'num_failed_logins': 0,
            'is_guest_login': 1,     
            'hot': 2,                
            'duration': 120,         
            'src_bytes': 200,
            'dst_bytes': 2000
        })
        
    return pkt

def generate_u2r():
    """Buffer Overflow U2R"""
    pkt = base_packet.copy()
    pkt.update({
        'protocol_type': 'tcp', 'service': 'telnet', 'flag': 'SF',
        'root_shell': 1, 'num_root': 3,
        'urgent': 2,
        'src_bytes': 1500,
        'dst_bytes': 200,
        'hot': 2,
        'logged_in': 1
    })
    return pkt

def run_attack(attack_type, duration):
    global BLOCKED
    if BLOCKED and attack_type != "Normal": 
        print("❌ Device is blocked. Cannot send attack traffic."); return

    print(f"\n🚀 Launching {attack_type} Traffic for {duration} seconds...")
    end_time = time.time() + duration
    count = 0
    
    while time.time() < end_time:
        if BLOCKED and attack_type != "Normal": break
        
        if attack_type == "DoS": 
            pkt = generate_dos()
            delay = 0.01 # 1000 pkts/sec (Fast but safe for Demo)
        elif attack_type == "Probe": 
            pkt = generate_probe()
            delay = 0.05
        elif attack_type == "R2L": 
            pkt = generate_r2l()
            delay = 0.1
        elif attack_type == "U2R": 
            pkt = generate_u2r()
            delay = 0.2
        elif attack_type == "Normal":
            pkt = generate_normal()
            delay = 0.1 # Normal traffic speed
        
        client.publish(TOPIC, json.dumps(pkt))
        count += 1
        if delay > 0: time.sleep(delay)
            
    print(f"\n✅ Complete. Sent {count} packets.")

def main():
    global BLOCKED
    print("Connecting to Broker...")
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_start()
    except Exception as e:
        print(f"❌ Connection Error: {e}"); sys.exit(1)

    while True:
        print(f"\n--- ⚔️ LIVE ATTACKER ({MY_IP}) ⚔️ ---")
        if BLOCKED: print("⚠️ STATUS: BLOCKED (Only Normal Traffic Allowed) ⚠️")
        else: print("✅ STATUS: CONNECTED")
        print("1. DoS | 2. Probe | 3. R2L | 4. U2R | 5. Normal | 6. Reset | 7. Exit")
        
        choice = input("Select: ")
        if choice == '7': break
        if choice == '6': BLOCKED = False; continue
        if BLOCKED and choice in ['1', '2', '3', '4']: 
            print("🚫 You are blocked! Reset connection first.")
            continue
        
        try:
            if choice in ['1','2','3','4', '5']:
                vec = {'1':'DoS','2':'Probe','3':'R2L','4':'U2R', '5':'Normal'}[choice]
                
                # --- INPUT DURATION ---
                dur_input = input("Enter duration in seconds (default 5): ")
                try:
                    duration = int(dur_input)
                except ValueError:
                    duration = 5 # Default if user just hits Enter
                
                run_attack(vec, duration)
        except Exception as e: 
            print(f"Error: {e}")

    client.loop_stop()

if __name__ == "__main__":
    main()