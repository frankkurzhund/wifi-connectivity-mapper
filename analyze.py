#!/usr/bin/env python3
"""
WiFi Mapper Analyzer
Merges GPS track (GPX) with measurement CSV and generates Ordinary Kriging heatmap.
"""

import pandas as pd
import gpxpy
import gpxpy.gpx
from pykrige.ok import OrdinaryKriging
import numpy as np
import matplotlib.pyplot as plt
import contextily as ctx
import geopandas as gpd
from shapely.geometry import Point
import os

def load_gpx(gpx_path):
    with open(gpx_path, 'r') as f:
        gpx = gpxpy.parse(f)
    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append({
                    'timestamp': point.time,
                    'lat': point.latitude,
                    'lon': point.longitude
                })
    df = pd.DataFrame(points)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    return df

def load_measurements(csv_path):
    df = pd.read_csv(csv_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.dropna(subset=['ping_avg_ms'])
    return df

def merge_data(gpx_df, meas_df):
    # Align by nearest timestamp (tolerance 10s)
    gpx_df = gpx_df.sort_values('timestamp')
    meas_df = meas_df.sort_values('timestamp')
    merged = pd.merge_asof(
        meas_df, gpx_df,
        on='timestamp',
        direction='nearest',
        tolerance=pd.Timedelta('10s')
    )
    return merged.dropna(subset=['lat', 'lon'])

def create_heatmap(merged_df, output_path='wifi_heatmap.png'):
    if len(merged_df) < 5:
        print("Not enough data points for interpolation.")
        return
    
    lons = merged_df['lon'].values
    lats = merged_df['lat'].values
    values = merged_df['ping_avg_ms'].values
    
    # Grid for interpolation
    grid_lon = np.linspace(lons.min(), lons.max(), 100)
    grid_lat = np.linspace(lats.min(), lats.max(), 100)
    
    OK = OrdinaryKriging(
        lons, lats, values,
        variogram_model='linear',
        verbose=False,
        enable_plotting=False,
        coordinates_type='geographic'
    )
    z, ss = OK.execute('grid', grid_lon, grid_lat)
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Create GeoDataFrame for basemap
    points = [Point(xy) for xy in zip(lons, lats)]
    gdf = gpd.GeoDataFrame(geometry=points, crs='EPSG:4326')
    gdf = gdf.to_crs(epsg=3857)
    
    # Interpolated grid as image
    extent = [lons.min(), lons.max(), lats.min(), lats.max()]
    im = ax.imshow(z, extent=extent, origin='lower', cmap='RdYlGn_r', alpha=0.7, aspect='auto')
    
    # Add basemap
    try:
        ctx.add_basemap(ax, crs='EPSG:4326', source=ctx.providers.OpenStreetMap.Mapnik)
    except:
        print("Could not add basemap (internet required).")
    
    # Scatter points
    ax.scatter(lons, lats, c=values, cmap='RdYlGn_r', s=20, edgecolors='k', linewidth=0.5)
    
    plt.colorbar(im, ax=ax, label='Ping (ms)')
    ax.set_title('WiFi Connectivity Heatmap (Ordinary Kriging)')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Heatmap saved to {output_path}")
    plt.show()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python analyze.py <measurements.csv> <track.gpx>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    gpx_path = sys.argv[2]
    
    print("Loading data...")
    gpx_df = load_gpx(gpx_path)
    meas_df = load_measurements(csv_path)
    merged = merge_data(gpx_df, meas_df)
    print(f"Merged {len(merged)} points")
    
    create_heatmap(merged)
