import paho.mqtt.client as mqtt
import json, time, random, hmac, hashlib, os

BROKER = "localhost"
PORT = 1883
USER = "edgeshield"
PASS = "123"
HMAC_KEY = b"edgeshield-secret-key-2026"

DEVICES = [
    {"id": "sensor-01", "type": "temperature", "unit": "degC", "mean": 22.5, "std": 1.2},
    {"id": "sensor-02", "type": "humidity",    "unit": "%",    "mean": 55.0, "std": 3.0},
    {"id": "sensor-03", "type": "pressure",    "unit": "hPa",  "mean": 1013.0, "std": 2.0},
]

fcnt = {d["id"]: 0 for d in DEVICES}

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
    else:
        print(f"[!] Connection failed: {rc}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(USER, PASS)
client.on_connect = on_connect
client.connect(BROKER, PORT, 60)
client.loop_start()

print("[*] EdgeShield Sensor Simulator started")
print("[*] Sending telemetry every 5 seconds...")

try:
    while True:
        for device in DEVICES:
            payload = make_payload(device)
            topic = f"iot/gateway/{payload['device_id']}/telemetry"
            client.publish(topic, json.dumps(payload))
            print(f"[+] {topic} -> value={payload['value']} rssi={payload['rssi']} fcnt={payload['fcnt']}")
        time.sleep(5)
except KeyboardInterrupt:
    print("\n[*] Simulator stopped")
    client.loop_stop()
