# EdgeShield

A layered-defence IoT gateway running on a **physical Raspberry Pi 5** — not a VM.
Cryptographic checks catch tampered and replayed messages; an unsupervised machine
learning layer catches what they cannot: behaviour that is valid but wrong.

**COM0453 Internet of Things — final project · Istanbul Kültür University · Spring 2026**
Berk Can Akbaba · Orhun Utku Topal

[Demo video](https://youtu.be/U_uwpmIvv90) · [Case study](https://www.orhunutkutopal.com/work/edgeshield.html)

---

## Why

The 2016 Mirai botnet took over hundreds of thousands of IoT devices — cameras,
thermostats, routers — because those devices had no serious defence at the edge.
Nearly a decade later most IoT deployments still trust the network and hope for the
best.

The point of EdgeShield is not any single component; all of these are known
techniques. The point is the composition: showing that an $80 board, configured
properly, can run all of these guarantees at once, from boot, in a way that survives
the field.

---

## Architecture

```
┌──────────────┐   MQTT over TLS   ┌─────────────────────────────┐   ┌─────────┐
│  3 simulated │ ────────────────▶ │     Raspberry Pi 5 gateway  │ ─▶│ SQLite  │
│   sensors    │   HMAC-signed     │                             │   └────┬────┘
└──────────────┘                   │  nftables  ·  Mosquitto     │        │
                                   │  Suricata IDS · collector   │        ▼
                                   │  Isolation Forest · API     │   ┌─────────┐
                                   └─────────────────────────────┘   │ Grafana │
                                                                     └─────────┘
```

Six services, all defined as `systemd` units — the device comes up ready to defend
itself after a power cut, with no manual steps.

---

## Defence layers

| Layer | Implementation | Catches |
|---|---|---|
| Firewall | `nftables`, stateful, with auto-blocking | Everything outside the ports and directions the gateway actually needs |
| Transport | Mosquitto MQTT with TLS + ACL | Eavesdropping; unauthenticated sensors |
| Message integrity | HMAC-SHA256 per payload | A single changed byte in transit |
| Replay protection | Per-sensor frame counter (FCnt), persisted in SQLite across reboots | An old but otherwise valid packet resent |
| Intrusion detection | Suricata IDS on the ingress interface, EVE JSON alerting | Port scans, known malicious patterns |
| Anomaly detection | Isolation Forest, trained on 480 windows per device | Behaviour that passes every cryptographic check but should not be happening |
| Observability | Flask REST API + Python collector → Grafana, 3 panels | — |

---

## Attack drill

Four scripts under `scripts/` serve as both validation and demo:

| Attack | Script | Result |
|---|---|---|
| Replay | `attack_replay.py` | Rejected in under a second, with an audit record |
| HMAC tampering | `attack_hmac.py` | Message never reaches the database |
| Port scan | `attack_portscan.sh` | Flagged by Suricata, source IP auto-blocked |
| Anomaly injection | `attack_anomaly.py` | Detected by Isolation Forest |

The anomaly case is deliberately subtle: the HMAC is correct and signal strength is
constant — only the packet rate rises. The affected sensor's anomaly score drops from
roughly 0.26 to 0.11 while the other sensors stay in their normal band, and the shift
lines up by timestamp in Grafana.

Evidence logs from real runs are in `logs/`.

---

## Stack

Raspberry Pi OS Lite 64-bit (Debian Trixie) · Python 3.11 · Flask · paho-mqtt ·
scikit-learn · Mosquitto 2.x · Suricata 7.x · nftables · Grafana 13.x · SQLite

---

## Running it

The gateway expects its secrets in the environment — nothing is hardcoded.

```bash
git clone https://github.com/OrhunX/edgeshield.git
cd edgeshield

cp .env.example .env     # then edit .env and set your own values
set -a && . ./.env && set +a

python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python3 scripts/collector.py &
python3 scripts/sensor_sim.py &
python3 scripts/api.py &
```

`EDGESHIELD_DB` and `EDGESHIELD_LOGS` default to `./data` and `./logs`, so the scripts
also run outside the Pi's directory layout.

### API endpoints

`/telemetry` · `/alerts` · `/stats` · `/health`

---

## Project report

A 15-page technical report covers the architecture, the defence layers, the four
attack scenarios and a system-level evaluation.

---

## License

MIT
