#!/bin/bash
echo "[*] PORT SCAN ATTACK SIMULATION"
echo "[*] Running nmap against localhost..."
nmap -sS -p 1-1000 127.0.0.1 2>&1 | tail -10
echo ""
echo "[*] Checking nftables blocked connections..."
sudo nft list ruleset | grep -A5 "blocklist"
echo ""
echo "[*] Checking Suricata alerts..."
sudo tail -5 /var/log/suricata/fast.log 2>/dev/null || echo "Suricata log henuz yok"
