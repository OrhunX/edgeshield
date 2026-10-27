import os
import paho.mqtt.client as mqtt
import json, time, hmac, hashlib, random

# ── Yapılandırma ───────────────────────────────────────────────
# Sırlar koda yazılmaz; ortam değişkeninden okunur. Örnek için .env.example
BROKER    = os.environ.get("EDGESHIELD_BROKER", "localhost")
PORT      = int(os.environ.get("EDGESHIELD_PORT", "1883"))
USER      = os.environ.get("EDGESHIELD_USER", "edgeshield")
PASS      = os.environ["EDGESHIELD_PASS"]
HMAC_KEY  = os.environ["EDGESHIELD_HMAC_KEY"].encode()
BASE      = os.environ.get("EDGESHIELD_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_FILE   = os.environ.get("EDGESHIELD_DB", os.path.join(BASE, "data", "edgeshield.db"))
LOG_DIR   = os.environ.get("EDGESHIELD_LOGS", os.path.join(BASE, "logs"))

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
