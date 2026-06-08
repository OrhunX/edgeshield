import paho.mqtt.client as mqtt
import json, time, random, hmac, hashlib, sqlite3

BROKER = "localhost"
PORT = 1883
USER = "edgeshield"
PASS = "123"
HMAC_KEY = b"edgeshield-secret-key-2026"
DB_FILE = "/home/orhunx/edgeshield/data/edgeshield.db"

DEVICES = [
    {"id": "sensor-01", "type": "temperature", "unit": "degC", "mean": 22.5, "std": 1.2},
    {"id": "sensor-02", "type": "humidity",    "unit": "%",    "mean": 55.0, "std": 3.0},
    {"id": "sensor-03", "type": "pressure",    "unit": "hPa",  "mean": 1013.0, "std": 2.0},
]

def get_start_fcnt(device_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        row = conn.execute("SELECT MAX(fcnt) FROM telemetry WHERE device_id=? AND alert_type=''", (device_id,)).fetchone()
        conn.close()
        return (row[0] or 0) + 1
    except:
        return 1

fcnt = {d["id"]: get_start_fcnt(d["id"]) for d in DEVICES}
print(f"[*] Starting fcnt: {fcnt}")

def make_payload(device):
    fcnt[device["id"]] += 1
    data = {
        "ts": int(time.time()),
        "device_id": device["id"],
        "sensor_type": device["type"],
        "value": round(random.gauss(device["mean"], device["std"]), 2),
        "unit": device["unit"],
        "rssi": random.randint(-95, -60),
        "fcnt": fcnt[device["id"]]
    }
    body = json.dumps(data, sort_keys=True).encode()
    mac = hmac.new(HMAC_KEY, body, hashlib.sha256).hexdigest()
    data["mac"] = mac
    return data

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[*] MQTT connected")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(USER, PASS)
client.on_connect = on_connect
client.connect(BROKER, PORT, 60)
client.loop_start()

print("[*] EdgeShield Sensor Simulator started")
try:
    while True:
        for device in DEVICES:
            payload = make_payload(device)
            topic = f"iot/gateway/{payload['device_id']}/telemetry"
            client.publish(topic, json.dumps(payload))
            print(f"[+] {topic} -> value={payload['value']} fcnt={payload['fcnt']}")
        time.sleep(5)
except KeyboardInterrupt:
    print("\n[*] Simulator stopped")
    client.loop_stop()
