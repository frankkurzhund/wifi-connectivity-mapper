#!/usr/bin/env python3
"""
Android Termux Full Signal Mapper
Live map + dashboard showing everything: WiFi APs, cellular towers, battery, GPS details, sensors.

Open http://localhost:5000 in your phone browser.
"""

import json
import subprocess
import time
import threading
from datetime import datetime
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)
points = []
latest = {}
lock = threading.Lock()

HTML = '''
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Full Signal Mapper</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
body { margin:0; font-family: system-ui; }
#map { height: 70vh; }
#panel { height: 30vh; overflow-y: auto; padding: 10px; background: #111; color: #eee; font-size: 13px; }
.good { color: #0f0; } .mid { color: #ff0; } .bad { color: #f00; }
</style>
</head>
<body>
<div id="map"></div>
<div id="panel">Loading...</div>
<script>
var map = L.map('map').setView([0, 0], 18);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
var markers = [];
var first = true;

function colorForRssi(rssi) {
  if (rssi > -50) return 'green';
  if (rssi > -65) return 'yellow';
  if (rssi > -80) return 'orange';
  return 'red';
}

function update() {
  fetch('/data').then(r => r.json()).then(data => {
    // Update map markers
    markers.forEach(m => map.removeLayer(m));
    markers = [];
    (data.points || []).forEach(p => {
      var m = L.circleMarker([p.lat, p.lon], {
        radius: 7,
        color: colorForRssi(p.rssi || -100),
        fillOpacity: 0.8
      }).addTo(map).bindPopup(
        '<b>' + (p.ssid || 'hidden') + '</b><br>RSSI: ' + p.rssi + ' dBm<br>Freq: ' + p.frequency + '<br>' + (p.capabilities || '')
      );
      markers.push(m);
    });
    if (data.points && data.points.length && first) {
      var last = data.points[data.points.length-1];
      map.setView([last.lat, last.lon], 18);
      first = false;
    }

    // Update panel
    var p = data.latest || {};
    var html = '<b>Latest snapshot</b><br>';
    if (p.location) html += 'GPS: ' + p.location.latitude.toFixed(5) + ', ' + p.location.longitude.toFixed(5) + ' (±' + (p.location.accuracy||'?') + 'm)<br>';
    if (p.battery) html += 'Battery: ' + p.battery.percentage + '% ' + (p.battery.plugged || '') + ' ' + (p.battery.temperature||'') + '°C<br>';
    if (p.wifi_conn) html += 'Connected: ' + (p.wifi_conn.ssid||'?') + ' | ' + (p.wifi_conn.rssi||'?') + ' dBm | ' + (p.wifi_conn.link_speed_mbps||'?') + ' Mbps<br>';
    if (p.wifi_count) html += 'Nearby WiFi APs: ' + p.wifi_count + '<br>';
    if (p.cell) html += 'Cellular: ' + (p.cell.type||'') + ' ' + (p.cell.dbm||'?') + ' dBm<br>';
    document.getElementById('panel').innerHTML = html;
  });
}
setInterval(update, 2000);
update();
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/data')
def get_data():
    with lock:
        return jsonify({"points": points[-300:], "latest": latest})

def run_cmd(cmd, timeout=8):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except Exception:
        pass
    return None

def logger_loop():
    print("Full mapper started. Open http://localhost:5000")
    while True:
        loc = run_cmd(["termux-location", "-p", "gps"])
        wifi = run_cmd(["termux-wifi-scaninfo"]) or []
        conn = run_cmd(["termux-wifi-connectioninfo"])
        cell = run_cmd(["termux-telephony-cellinfo"])
        batt = run_cmd(["termux-battery-status"])

        with lock:
            latest["location"] = loc
            latest["battery"] = batt
            latest["wifi_conn"] = conn
            latest["wifi_count"] = len(wifi)
            if cell and isinstance(cell, list) and cell:
                # Prefer registered cell
                reg = next((c for c in cell if c.get("registered")), cell[0])
                latest["cell"] = reg
            else:
                latest["cell"] = None

            if loc and wifi:
                for net in wifi:
                    points.append({
                        "lat": loc.get("latitude"),
                        "lon": loc.get("longitude"),
                        "ssid": net.get("ssid"),
                        "bssid": net.get("bssid"),
                        "rssi": net.get("rssi"),
                        "frequency": net.get("frequency"),
                        "capabilities": net.get("capabilities"),
                        "time": datetime.utcnow().isoformat()
                    })

        best = max((n.get("rssi", -100) for n in wifi), default=-100) if wifi else "N/A"
        print(f"{datetime.now().strftime('%H:%M:%S')} | APs:{len(wifi)} | best:{best}")
        time.sleep(5)

if __name__ == "__main__":
    t = threading.Thread(target=logger_loop, daemon=True)
    t.start()
    app.run(host="127.0.0.1", port=5000, debug=False)
