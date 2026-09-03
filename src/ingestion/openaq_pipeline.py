"""
OpenAQ Static Data Pipeline for Kathmandu AQI Project
=======================================================
STATIC VERSION: pulls full historical data ONCE and saves it as a fixed CSV.
No auto-updating yet.
 
Usage:
    python openaq_pipeline.py --location_id 12345 --start 2017-01-01 --end 2025-12-31 --out data/raw/sorakhutte.csv
 
"""

import os
import time
import argparse
from datetime import datetime, timedelta, timezone

import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv() #reads .env file and loads OPENAQ_API_KEY into environment variables

BASE_URL = "https://api.openaq.org/v3"
API_KEY = os.environ.get("OPENAQ_API_KEY")  # Get the API key from environment variables    

if not API_KEY:
    raise ValueError("OPENAQ_API_KEY is not set in the environment variables. Please set it in the .env file.")

HEADERS = {"X-API-Key": API_KEY}

def get_sensors_for_location(location_id: int):
    """ Return list of sensors dicts (id, parameter, units) for a given location_id. """
    url = f"{BASE_URL}/locations/{location_id}/sensors"
    response = requests.get(url, headers=HEADERS, params={"limit":1000}, timeout=30)

    response.raise_for_status()  #To ensure successful response, raise an error if the request failed

    results = response.json().get("results", [])
    sensors = []
    for r in results:
        sensors.append({
            "sensor_id": r["id"],
            "parameter":r["parameter"]["name"],
            "units": r["parameter"]["units"],
        })
    return sensors

def fetch_sensor_measurements(sensor_id: int, date_from: str, date_to: str):
    """ Pull all hourly measurements for one sensor within a date range. Handling Pagination."""
    all_rows = []
    page = 1
    while True:
        url = f"{BASE_URL}/sensors/{sensor_id}/hours"   # To get hourly measurements for a sensor
        params = {
            "datetime_from":date_from,
            "datetime_to":date_to,
            "limit":1000,
            "page":page,
        }

        response = requests.get(url, headers=HEADERS, params=params, timeout=30)

        if response.status_code == 429:
            print("Rate limit exceeded, Sleeping for 10 seconds...")
            time.sleep(10)
            continue

        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()
        results = data.get("results", [])
        if not results:
            break
        for r in results:
            all_rows.append({
                "datetime_utc":r["period"]["datetimeFrom"]["utc"],
                "value":r["value"],
                "parameter":r["parameter"]["name"],
                "units":r["parameter"]["units"],
            })

        found = data.get("meta", {}).get("found", 0)
        if isinstance(found, int) and page * 1000 >= found:
            break
        page+=1
        time.sleep(0.5)  # Sleep to avoid hitting rate limits
    return all_rows

def backfill(location_id: int, start: str, end: str, out_path: str):
    """ Pull the historical range once andsave it as a static CSV."""

    print(f"Fetching sensors for location {location_id}...")
    sensors = get_sensors_for_location(location_id)
    print(f"Found {len(sensors)} sensors: {[s['parameter'] for s in sensors]}")

    # Converting typed-in date strings (like "2017-01-01") into actual date objects
    start_date = datetime.strptime(start, "%Y-%m-%d")  
    end_date = datetime.strptime(end, "%Y-%m-%d")

    all_data = []
    for sensor in sensors:
        print(f"Pulling parameter: {sensor['parameter']} (sensor {sensor['sensor_id']})")
        current = start_date
        while current < end_date:
            chunk_end = min(current +timedelta(days=365), end_date)
            date_from = current.strftime("%Y-%m-%dT00:00:00Z")
            date_to = chunk_end.strftime("%Y-%m-%dT00:00:00Z")
            print(f"{date_from} to {date_to}")
            rows = fetch_sensor_measurements(sensor["sensor_id"], date_from, date_to)
            all_data.extend(rows)
            current = chunk_end

    df = pd.DataFrame(all_data)
    if df.empty:
        print("No data fetched. Check the location_id and date range.")
        return

    df = df.pivot_table(index="datetime_utc", columns="parameter", values="value", aggfunc='mean').reset_index()
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pull a static historical AQI dataset from OpenAQ for one station.")
    parser.add_argument("--location_id", type=int, required=True, help="OpenAQ location ID (find via explore.openaq.org)")
    parser.add_argument("--start", type=str, default="2017-01-01", help="Start date, YYYY-MM-DD")
    parser.add_argument("--end", type=str, default=datetime.now(timezone.utc).strftime("%Y-%m-%d"), help="End date, YYYY-MM-DD")
    parser.add_argument("--out", type=str, required=True, help="Output CSV path, e.g. data/raw/sorakhutte.csv")
    args = parser.parse_args()
 
    backfill(args.location_id, args.start, args.end, args.out)


