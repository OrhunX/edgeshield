# EdgeShield — Raspberry Pi 5 IoT Security Gateway

**COM0453 Internet of Things — Final Project**
Istanbul Kultur University | Spring 2026

**Team:** Berk Can Akbaba (2200004131) · Orhun Utku Topal (2200003909)

## Overview
EdgeShield is a multi-layer secure IoT gateway running on Raspberry Pi 5.
It intercepts all IoT traffic, enforces firewall rules, verifies payload
integrity, detects intrusions, and visualizes telemetry in real time.

## Architecture
[Simulated Sensors] → MQTT → [RPi5 Gateway] → SQLite → [Grafana Dashboard]
|
nftables + Suricata + HMAC
## Features
- Mosquitto MQTT broker with TLS + ACL
- nftables stateful firewall with auto-blocking
- HMAC-SHA256 payload integrity verification
- FCnt-based replay attack protection
- Suricata IDS with EVE JSON alerting
- Isolation Forest anomaly detection (AI)
- Grafana dashboard (3 panels)
- 3-device sensor simulator

## Stack
- OS: Raspberry Pi OS Lite 64-bit (Debian Trixie)
- Python 3.11, Flask, paho-mqtt, scikit-learn
- Mosquitto 2.x, Suricata 7.x, nftables
- Grafana 13.x, SQLite

## Quick Start
```bash
git clone https://github.com/OrhunX/edgeshield.git
cd edgeshield
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 scripts/collector.py &
python3 scripts/sensor_sim.py &
python3 scripts/api.py &
```

## Security Scenarios
| Attack | Detection | Mitigation |
|--------|-----------|------------|
| Replay attack | FCnt check | Packet dropped |
| Port scan | Suricata IDS | IP auto-blocked |
| HMAC tampering | HMAC-SHA256 | Message rejected |
| Anomaly injection | Isolation Forest | Alert generated |

## License
MIT

## Demo Video
https://youtu.be/U_uwpmIvv90?si=KQZWO4nHQ9xAwUVk
