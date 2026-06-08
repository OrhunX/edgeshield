import paho.mqtt.client as mqtt
import json, hmac, hashlib, time, sqlite3, os
from datetime import datetime

BROKER = "localhost"
PORT = 1883
USER = "edgeshield"
PASS = "123"
HMAC_KEY = b"edgeshield-secret-key-2026"
LOG_FILE = "/home/orhunx/edgeshield/logs/collector.log"
DB_FILE = "/home/orhunx/edgeshield/data/edgeshield.db"

os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER, device_id TEXT, sensor_type TEXT,
        value REAL, unit TEXT, rssi INTEGER, fcnt INTEGER,
        alert_level TEXT, alert_type TEXT
    )''')
    conn.commit()
    conn.close()

def get_last_fcnt(device_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    row = c.execute("SELECT MAX(fcnt) FROM telemetry WHERE device_id=? AND alert_type=''", (device_id,)).fetchone()
    conn.close()
    return row[0] if row[0] is not None else -1

def insert_db(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO telemetry
        (ts, device_id, sensor_type, value, unit, rssi, fcnt, alert_level, alert_type)
        VALUES (?,?,?,?,?,?,?,?,?)''', (
        data.get("ts"), data.get("device_id"), data.get("sensor_type"),
        data.get("value"), data.get("unit"), data.get("rssi"),
        data.get("fcnt"), data.get("alert_level","info"), data.get("alert_type","")
    ))
    conn.commit()
    conn.close()

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def verify_hmac(payload_dict):
    received_mac = payload_dict.pop("mac", None)
    if not received_mac:
        return False
    body = json.dumps(payload_dict, sort_keys=True).encode()
    expected = hmac.new(HMAC_KEY, body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received_mac)

def on_message(client, userdata, msg):
    try:
        raw = json.loads(msg.payload.decode())
        device_id = raw.get("device_id", "unknown")
        fcnt = raw.get("fcnt", 0)

        payload_copy = raw.copy()
        if not verify_hmac(payload_copy):
            log(f"[INTEGRITY_FAIL] device={device_id} topic={msg.topic}")
            insert_db({"ts": int(time.time()), "device_id": device_id,
                      "alert_level": "critical", "alert_type": "INTEGRITY_FAIL"})
            return

        last = get_last_fcnt(device_id)
        if fcnt <= last:
            log(f"[REPLAY_DETECTED] device={device_id} fcnt={fcnt} last_known={last}")
            insert_db({"ts": int(time.time()), "device_id": device_id,
                      "alert_level": "critical", "alert_type": "REPLAY_DETECTED",
                      "fcnt": fcnt})
            return

        value = raw.get("value", 0)
        sensor_type = raw.get("sensor_type", "")
        out_of_range = False
        if sensor_type == "temperature" and not (-40 <= value <= 85):
            out_of_range = True
        elif sensor_type == "humidity" and not (0 <= value <= 100):
            out_of_range = True
        elif sensor_type == "pressure" and not (800 <= value <= 1200):
            out_of_range = True

        if out_of_range:
            raw["alert_level"] = "warning"
            raw["alert_type"] = "OUT_OF_RANGE"
            log(f"[OUT_OF_RANGE] device={device_id} value={value}")
        else:
            raw["alert_level"] = "info"
            raw["alert_type"] = ""
            log(f"[OK] device={device_id} type={sensor_type} value={value} fcnt={fcnt}")

        insert_db(raw)

    except Exception as e:
        log(f"[ERROR] {e}")

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        client.subscribe("iot/gateway/#")
        log("[*] Collector connected")

init_db()
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(USER, PASS)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
log("[*] EdgeShield Collector started")
client.loop_forever()
