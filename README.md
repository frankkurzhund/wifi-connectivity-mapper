# WiFi Connectivity Mapper

Modern recreation of [AlbyHojel's WiFi mapper](https://github.com/alhojel/wifi_mapper).

Walk around with a laptop + phone GPS tracker, log network performance, then generate beautiful Ordinary Kriging heatmaps of connectivity.

## How it works

1. Start a GPS tracking app on your phone (e.g. GPX Tracker, or any app that exports GPX).
2. Run `python logger.py` on your laptop. It logs ping latency every 5 seconds to `wifi_measurements.csv`.
3. Walk around the area you want to map.
4. Stop both, export the GPX file from your phone.
5. Run the analyzer: `python analyze.py wifi_measurements.csv your_track.gpx`

The analyzer aligns the measurements with GPS points by timestamp and uses Ordinary Kriging to interpolate a full coverage heatmap.

## Setup

```bash
pip install -r requirements.txt
```

## Files

- `logger.py` — Continuous ping logger (cross-platform).
- `analyze.py` — Merges CSV + GPX and generates the heatmap.
- `requirements.txt`

## Notes

- Best results with even coverage while walking.
- Speedtest can be added later if desired (original had it every 5 min).
- On Linux you can optionally extend logger to capture WiFi RSSI via `nmcli` or `iw`.

Inspired by the original post: https://x.com/AlbyHojel/status/1850622067680645364
