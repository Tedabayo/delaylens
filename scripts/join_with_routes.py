import os
import pandas as pd

IN_CSV = "data/processed/realtime_enriched.csv"
ROUTES_TXT = "data/static/google_transit/routes.txt"
OUT_CSV = "data/processed/realtime_enriched_with_routes.csv"

def main():
    df = pd.read_csv(IN_CSV, dtype={"route_id": "string", "stop_id": "string", "trip_id": "string"})
    routes = pd.read_csv(ROUTES_TXT, dtype={"route_id": "string"})

    # Keep only useful route columns (these exist in GTFS)
    keep_cols = ["route_id", "route_short_name", "route_long_name", "route_type"]
    routes = routes[[c for c in keep_cols if c in routes.columns]].copy()

    out = df.merge(routes, on="route_id", how="left")

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    print("Rows:", len(out))
    print("Rows with route_long_name:", out.get("route_long_name").notna().sum() if "route_long_name" in out.columns else "N/A")
    print("\nSample:")
    cols = ["iso_time_utc", "route_id", "route_short_name", "route_long_name", "stop_name", "delay_seconds"]
    cols = [c for c in cols if c in out.columns]
    print(out[cols].head(10))

if __name__ == "__main__":
    main()
