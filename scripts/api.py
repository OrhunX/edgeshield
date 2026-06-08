from flask import Flask, jsonify
import sqlite3, os

app = Flask(__name__)
DB_FILE = "/home/orhunx/edgeshield/data/edgeshield.db"

def query(sql, args=()):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, args).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.route("/telemetry")
def telemetry():
    return jsonify(query("SELECT * FROM telemetry ORDER BY ts DESC LIMIT 200"))

@app.route("/alerts")
def alerts():
    return jsonify(query("SELECT * FROM telemetry WHERE alert_level IN ('warning','critical') ORDER BY ts DESC LIMIT 100"))

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/stats")
def stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM telemetry").fetchone()[0]
    alerts = c.execute("SELECT COUNT(*) FROM telemetry WHERE alert_level != 'info'").fetchone()[0]
    devices = c.execute("SELECT COUNT(DISTINCT device_id) FROM telemetry").fetchone()[0]
    conn.close()
    return jsonify({"total_records": total, "total_alerts": alerts, "active_devices": devices})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
