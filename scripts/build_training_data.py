import os
import pandas as pd

IN_CSV = "data/processed/realtime_enriched_with_routes.csv"
OUT_CSV = "data/processed/training_data.csv"

def main():
    df = pd.read_csv(IN_CSV)

    # Parse timestamp
    df["iso_time_utc"] = pd.to_datetime(df["iso_time_utc"], errors="coerce")
    df["hour"] = df["iso_time_utc"].dt.hour

    # Drop rows without hour (safety)
    df = df[df["hour"].notna()].copy()

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    print("Training rows:", len(df))
    print("Hour distribution:")
    print(df["hour"].value_counts().sort_index())
    print("\nSample:")
    print(df[["iso_time_utc", "route_id", "stop_name", "hour"]].head(10))

if __name__ == "__main__":
    main()
