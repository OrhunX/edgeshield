import paho.mqtt.client as mqtt
import json, time, hmac, hashlib, random

BROKER = "localhost"
PORT = 1883
USER = "edgeshield"
PASS = "123"
HMAC_KEY = b"edgeshield-secret-key-2026"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(USER, PASS)
client.connect(BROKER, PORT, 60)
client.loop_start()

print("[*] ANOMALY INJECTION ATTACK")
print("[*] Sending high-rate packets with fixed RSSI (software radio simulation)...")

fcnt = 99000
for i in range(50):
    fcnt += 1
    data = {
        "ts": int(time.time()),
        "device_id": "sensor-01",
        "sensor_type": "temperature",
        "value": round(random.gauss(22.5, 0.01), 2),
        "unit": "degC",
        "rssi": -72,
        "fcnt": fcnt
    }
    body = json.dumps(data, sort_keys=True).encode()
    mac = hmac.new(HMAC_KEY, body, hashlib.sha256).hexdigest()
    data["mac"] = mac
    client.publish("iot/gateway/sensor-01/telemetry", json.dumps(data))
    if i % 10 == 0:
        print(f"[!] Sent {i+1}/50 anomalous packets (fixed rssi=-72, low variance)")
    time.sleep(0.1)

print("[*] Done. Wait 30s for anomaly detector to flag...")
client.loop_stop()
