#!/usr/bin/env python3
"""
Android Termux WiFi Signal Mapper
Logs true WiFi signal strength (RSSI of nearby APs) + GPS location while you walk.

Requirements:
- Termux + Termux:API (from F-Droid)
- Location permission granted to Termux:API
- WiFi enabled
"""

import json
import subprocess
import time
import csv
from datetime import datetime
import os

CSV_FILE = "wifi_signal_log.csv"
INTERVAL = 5  # seconds between scans

def get_location():
    try:
        result = subprocess.run(
            ["termux-location", "-p", "gps"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            return data.get("latitude"), data.get("longitude"), data.get("accuracy")
    except Exception as e:
        print(f"Location error: {e}")
    return None, None, None

def get_wifi_scan():
    try:
        result = subprocess.run(
            ["termux-wifi-scaninfo"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except Exception as e:
        print(f"WiFi scan error: {e}")
    return []

def main():
    print("Starting Android WiFi Signal Mapper")
    print("Walk around. Press Ctrl+C to stop.")
    print(f"Logging to {CSV_FILE}\n")

    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "timestamp", "latitude", "longitude", "accuracy",
                "ssid", "bssid", "rssi_dbm", "frequency_mhz", "capabilities"
            ])

        try:
            while True:
                ts = datetime.utcnow().isoformat()
                lat, lon, acc = get_location()
                networks = get_wifi_scan()

                if lat is not None and networks:
                    for net in networks:
                        writer.writerow([
                            ts,
                            lat,
                            lon,
                            acc,
                            net.get("ssid", ""),
                            net.get("bssid", ""),
                            net.get("rssi", ""),
                            net.get("frequency", ""),
                            net.get("capabilities", "")
                        ])
                    f.flush()
                    print(f"{ts} | {lat:.5f},{lon:.5f} | {len(networks)} networks | best RSSI: {max((n.get('rssi', -100) for n in networks), default='N/A')}")
                else:
                    print(f"{ts} | No location or no networks")

                time.sleep(INTERVAL)

        except KeyboardInterrupt:
            print("\nStopped. Data saved to", CSV_FILE)

if __name__ == "__main__":
    main()
