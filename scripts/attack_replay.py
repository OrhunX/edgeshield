import paho.mqtt.client as mqtt
import json, time, hmac, hashlib

BROKER = "localhost"
PORT = 1883
USER = "edgeshield"
PASS = "123"
HMAC_KEY = b"edgeshield-secret-key-2026"

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
