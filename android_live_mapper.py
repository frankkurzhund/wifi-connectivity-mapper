#!/usr/bin/env python3
"""
Android Termux Live WiFi Signal Mapper
Logs true RSSI of nearby APs + GPS and serves a live map in your phone browser.

Open http://localhost:5000 in your browser while it runs.
"""

import json
import subprocess
import time
import threading
from datetime import datetime
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)
points = []  # list of dicts
lock = threading.Lock()

HTML = '''
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Live WiFi Map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
body { margin:0; }
#map { height: 100vh; }
</style>
</head>
<body>
<div id="map"></div>
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
  fetch('/points').then(r => r.json()).then(data => {
    markers.forEach(m => map.removeLayer(m));
    markers = [];
    data.forEach(p => {
      var m = L.circleMarker([p.lat, p.lon], {
        radius: 8,
        color: colorForRssi(p.rssi),
        fillOpacity: 0.7
      }).addTo(map).bindPopup(p.ssid + '<br>RSSI: ' + p.rssi + ' dBm');
      markers.push(m);
    });
    if (data.length && first) {
      map.setView([data[data.length-1].lat, data[data.length-1].lon], 18);
      first = false;
    }
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

@app.route('/points')
def get_points():
    with lock:
        return jsonify(points[-200:])  # last 200 points

def get_location():
    try:
        result = subprocess.run(["termux-location", "-p", "gps"], capture_output=True, text=True, timeout=8)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            return data.get("latitude"), data.get("longitude")
    except:
        pass
    return None, None

def get_wifi_scan():
    try:
        result = subprocess.run(["termux-wifi-scaninfo"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except:
        pass
    return []

def logger_loop():
    print("Logger started. Open http://localhost:5000 in your browser.")
    while True:
        lat, lon = get_location()
        networks = get_wifi_scan()
        if lat is not None and networks:
            with lock:
                for net in networks:
                    points.append({
                        "lat": lat,
                        "lon": lon,
                        "ssid": net.get("ssid", "hidden"),
                        "rssi": net.get("rssi", -100),
                        "time": datetime.utcnow().isoformat()
                    })
            best = max((n.get("rssi", -100) for n in networks), default=-100)
            print(f"{datetime.now().strftime('%H:%M:%S')} | {lat:.5f},{lon:.5f} | {len(networks)} APs | best {best} dBm")
        time.sleep(5)

if __name__ == "__main__":
    t = threading.Thread(target=logger_loop, daemon=True)
    t.start()
    app.run(host="127.0.0.1", port=5000, debug=False)
