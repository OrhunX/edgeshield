import paho.mqtt.client as mqtt
import json, time

BROKER = "localhost"
PORT = 1883
USER = "edgeshield"
PASS = "123"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(USER, PASS)
client.connect(BROKER, PORT, 60)
client.loop_start()

print("[*] HMAC TAMPERING ATTACK SIMULATION")
print("[*] Sending tampered payload (wrong MAC)...")

for i in range(5):
    tampered = {
        "ts": int(time.time()),
        "device_id": "sensor-01",
        "sensor_type": "temperature",
        "value": 99.9,
        "unit": "degC",
        "rssi": -70,
        "fcnt": 9999 + i,
        "mac": "fakemac000000000000000000000000000000000000000000000000000000000"
    }
    client.publish("iot/gateway/sensor-01/telemetry", json.dumps(tampered))
    print(f"[!] Tampered packet {i+1} sent (value=99.9, fake MAC)")
    time.sleep(1)

print("[*] Done. Check logs for INTEGRITY_FAIL alerts.")
client.loop_stop()
