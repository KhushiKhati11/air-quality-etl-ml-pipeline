import os
import argparse
from datetime import datetime
 
import requests
import pandas as pd
 
BASE_URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"
 
# Temperature, relative humidity, wind speed, wind direction, precipitation
PARAMETERS = ["T2M", "RH2M", "WS10M", "WD10M", "PRECTOTCORR"]
 
 
def fetch_weather(lat: float, lon: float, start: str, end: str):
    """Pull hourly weather data for one coordinate and date range."""
    params = {
        "parameters": ",".join(PARAMETERS),
        "community": "RE",
        "longitude": lon,
        "latitude": lat,
        "start": start,
        "end": end,
        "format": "JSON",
        "time-standard": "UTC",
    }
    response = requests.get(BASE_URL, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()
 
    parameter_data = data["properties"]["parameter"]
 
    rows = []
    timestamps = list(parameter_data[PARAMETERS[0]].keys())
    for ts in timestamps:
        row = {"datetime_utc": ts}
        for param in PARAMETERS:
            row[param] = parameter_data[param].get(ts)
        rows.append(row)
 
    df = pd.DataFrame(rows)
    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], format="%Y%m%d%H")
    return df
 
 
def backfill(lat: float, lon: float, start: str, end: str, out_path: str):
    print(f"Fetching weather for ({lat}, {lon}), {start} to {end}...")
    df = fetch_weather(lat, lon, start, end)
 
    if df.empty:
        print("No data returned. Check coordinates and date range.")
        return
 
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")
 
 
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pull hourly NASA POWER weather data for one coordinate.")
    parser.add_argument("--lat", type=float, required=True, help="Latitude")
    parser.add_argument("--lon", type=float, required=True, help="Longitude")
    parser.add_argument("--start", type=str, required=True, help="Start date, YYYYMMDD")
    parser.add_argument("--end", type=str, required=True, help="End date, YYYYMMDD")
    parser.add_argument("--out", type=str, required=True, help="Output CSV path")
    args = parser.parse_args()
 
    backfill(args.lat, args.lon, args.start, args.end, args.out)