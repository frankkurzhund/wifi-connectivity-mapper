# Phone-Only WiFi Mapper (Android via Termux)

You can do the full mapping process on your Android phone using Termux.

## Quick Recommendation

For the easiest polished experience, install **NetLens** from the Play Store:
https://play.google.com/store/apps/details?id=com.netlens

It does live AR heatmaps of your WiFi signal as you walk around. Everything stays on your phone.

## Custom Open-Source Version (Termux)

### 1. Install Termux + Termux:API
- Install Termux from F-Droid (not Play Store)
- Install Termux:API from F-Droid
- Grant location and nearby devices permissions

### 2. Install dependencies
```bash
pkg update && pkg upgrade
pkg install python git termux-api
pip install pandas matplotlib pykrige
```

### 3. Clone this repo
```bash
git clone https://github.com/frankkurzhund/wifi-connectivity-mapper
cd wifi-connectivity-mapper
```

### 4. Use an existing scanner or the logger
Best existing tool: [Termux-WiFi-map](https://github.com/BuriXon-code/Termux-WiFi-map)

```bash
git clone https://github.com/BuriXon-code/Termux-WiFi-map
cd Termux-WiFi-map
chmod +x termux-wifi-map
./termux-wifi-map --run --continuous -d 5
# Walk around, then Ctrl+C
./termux-wifi-map --save -n my_map -f csv
```

Export as KML and open in Google Earth, or CSV for analysis.

### 5. Analyze with the included tools
You can adapt analyze.py to load the CSV from Termux-WiFi-map and plot signal strength heatmaps.

For a pure ping + GPS version (closer to original AlbyHojel), you can run a modified logger that uses `termux-location` instead of external GPX.
