#!/usr/bin/env python3
"""
WiFi Mapper Logger - Cross-platform
Logs ping latency and packet loss while you walk around.
Pair with a GPS tracker app that exports GPX, then run the analyzer.
"""

import time
import csv
import subprocess
import platform
from datetime import datetime
import os

CSV_FILE = "wifi_measurements.csv"
PING_TARGET = "8.8.8.8"
PING_INTERVAL = 5  # seconds

def ping_host(host=PING_TARGET, count=4):
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", str(count), host]
    else:
        cmd = ["ping", "-c", str(count), host]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        output = result.stdout
        
        avg_ms = None
        loss = 0.0
        for line in output.splitlines():
            line_lower = line.lower()
            if "avg" in line_lower or "average" in line_lower:
                parts = line.replace("=", " ").split()
                for i, p in enumerate(parts):
                    if p.lower() in ("avg", "average") and i + 1 < len(parts):
                        try:
                            avg_ms = float(parts[i + 1].replace("ms", ""))
                        except ValueError:
                            pass
            if "packet loss" in line_lower or "% packet" in line_lower:
                if "%" in line:
                    try:
                        loss = float(line.split("%")[0].split()[-1])
                    except:
                        pass
        return avg_ms, loss
    except Exception as e:
        print(f"Ping error: {e}")
        return None, None

def main():
    print("Starting WiFi mapper logger. Walk around your area!")
    print("Press Ctrl+C to stop. Use a GPX GPS tracker app on your phone at the same time.")
    
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "ping_avg_ms", "packet_loss_pct"])
        
        while True:
            ts = datetime.utcnow().isoformat()
            avg, loss = ping_host()
            writer.writerow([ts, avg if avg is not None else "", loss])
            f.flush()
            print(f"{ts} | Ping: {avg} ms | Loss: {loss}%")
            time.sleep(PING_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped. Measurements saved to", CSV_FILE)
