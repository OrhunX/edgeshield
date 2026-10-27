import os
import paho.mqtt.client as mqtt
import json, time, hmac, hashlib

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

def make_payload(device_id, value, fcnt):
    data = {
        "ts": int(time.time()),
        "device_id": device_id,
        "sensor_type": "temperature",
        "value": value,
        "unit": "degC",
        "rssi": -75,
        "fcnt": fcnt
    }
    body = json.dumps(data, sort_keys=True).encode()
    mac = hmac.new(HMAC_KEY, body, hashlib.sha256).hexdigest()
    data["mac"] = mac
    return data

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(USER, PASS)
client.connect(BROKER, PORT, 60)
client.loop_start()

print("[*] REPLAY ATTACK SIMULATION")
print("[*] Sending legitimate packet with fcnt=100...")
payload = make_payload("sensor-01", 22.5, 100)
client.publish("iot/gateway/sensor-01/telemetry", json.dumps(payload))
time.sleep(1)

print("[*] Replaying same packet (fcnt=100) 5 times...")
for i in range(5):
    payload = make_payload("sensor-01", 22.5, 100)
    client.publish("iot/gateway/sensor-01/telemetry", json.dumps(payload))
    print(f"[!] Replay attempt {i+1} sent (fcnt=100)")
    time.sleep(1)

print("[*] Done. Check logs for REPLAY_DETECTED alerts.")
client.loop_stop()
