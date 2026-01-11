import os
import pandas as pd

REALTIME_CSV = "data/raw/trip_updates.csv"
STOPS_TXT = "data/static/google_transit/stops.txt"
OUT_CSV = "data/processed/realtime_enriched.csv"

def main():
    # Load realtime
    rt = pd.read_csv(REALTIME_CSV, dtype={"stop_id": "string", "trip_id": "string", "route_id": "string"})
    # Some rows can have missing stop_id
    rt["stop_id"] = rt["stop_id"].astype("string")

    # Load stops
    stops = pd.read_csv(STOPS_TXT, dtype={"stop_id": "string"})
    stops = stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]].copy()

    # Join
    enriched = rt.merge(stops, on="stop_id", how="left")

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    enriched.to_csv(OUT_CSV, index=False)

    print("Realtime rows:", len(rt))
    print("Enriched rows:", len(enriched))
    print("Rows with stop_name:", enriched["stop_name"].notna().sum())
    print("\nSample enriched rows:")
    print(enriched[["iso_time_utc", "route_id", "trip_id", "stop_id", "stop_name", "delay_seconds"]].head(10))

if __name__ == "__main__":
    main()
