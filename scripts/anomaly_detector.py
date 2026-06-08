import sqlite3, time, json
import numpy as np
from sklearn.ensemble import IsolationForest
from datetime import datetime

DB_FILE = "/home/orhunx/edgeshield/data/edgeshield.db"
LOG_FILE = "/home/orhunx/edgeshield/logs/anomaly.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def get_features(device_id, limit=200):
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute("""
        SELECT ts, rssi, fcnt, value FROM telemetry 
        WHERE device_id=? AND alert_type='' AND rssi IS NOT NULL
        ORDER BY ts DESC LIMIT ?
    """, (device_id, limit)).fetchall()
    conn.close()
    if len(rows) < 10:
        return None
    ts_vals   = [r[0] for r in rows]
    rssi_vals = [r[1] for r in rows]
    fcnt_vals = [r[2] for r in rows]
    mean_rssi = np.mean(rssi_vals)
    std_rssi  = np.std(rssi_vals)
    intervals = [abs(ts_vals[i]-ts_vals[i+1]) for i in range(len(ts_vals)-1)]
    mean_interval = np.mean(intervals)
    fcnt_diffs = [abs(fcnt_vals[i]-fcnt_vals[i+1]) for i in range(len(fcnt_vals)-1)]
    fcnt_rate = np.mean(fcnt_diffs)
    return [mean_rssi, std_rssi, mean_interval, fcnt_rate]

def train_model(device_id):
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute("""
        SELECT ts, rssi, fcnt FROM telemetry
        WHERE device_id=? AND alert_type='' AND rssi IS NOT NULL
        ORDER BY ts ASC LIMIT 500
    """, (device_id,)).fetchall()
    conn.close()
    if len(rows) < 50:
        return None
    features = []
    window = 20
    for i in range(window, len(rows)):
        chunk = rows[i-window:i]
        ts_v    = [r[0] for r in chunk]
        rssi_v  = [r[1] for r in chunk]
        fcnt_v  = [r[2] for r in chunk]
        intervals = [abs(ts_v[j]-ts_v[j+1]) for j in range(len(ts_v)-1)]
        fcnt_diffs = [abs(fcnt_v[j]-fcnt_v[j+1]) for j in range(len(fcnt_v)-1)]
        features.append([
            np.mean(rssi_v),
            np.std(rssi_v),
            np.mean(intervals),
            np.mean(fcnt_diffs)
        ])
    if len(features) < 10:
        return None
    model = IsolationForest(n_estimators=100, contamination=0.02, random_state=42)
    model.fit(features)
    log(f"[*] Model trained for {device_id} with {len(features)} windows")
    return model

def detect(device_id, model):
    features = get_features(device_id)
    if features is None:
        return
    score = model.decision_function([features])[0]
    pred  = model.predict([features])[0]
    if score < 0.15:
        log(f"[ANOMALY] device={device_id} score={score:.4f} features={[round(f,2) for f in features]}")
        conn = sqlite3.connect(DB_FILE)
        conn.execute("""INSERT INTO telemetry (ts, device_id, alert_level, alert_type)
                        VALUES (?,?,'critical','ANOMALY_DETECTED')""",
                     (int(time.time()), device_id))
        conn.commit()
        conn.close()
    else:
        log(f"[NORMAL] device={device_id} score={score:.4f}")

DEVICES = ["sensor-01", "sensor-02", "sensor-03"]

log("[*] Training anomaly detection models...")
models = {}
for d in DEVICES:
    m = train_model(d)
    if m:
        models[d] = m
    else:
        log(f"[!] Not enough data for {d}")

log(f"[*] Models ready: {list(models.keys())}")
log("[*] Starting detection loop (every 30s)...")

while True:
    for d in DEVICES:
        if d in models:
            detect(d, models[d])
    time.sleep(30)
