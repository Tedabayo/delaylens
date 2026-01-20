# scripts/compute_gap_seconds.py
import os
import pandas as pd

IN_CSV = "data/raw/trip_updates.csv"
OUT_CSV = "data/processed/realtime_with_gap.csv"

PRIMARY_COLS = ["feed_timestamp", "iso_time_utc", "route_id", "stop_id", "trip_id"]

def main():
    if not os.path.exists(IN_CSV):
        raise FileNotFoundError(f"Missing {IN_CSV}. Run fetch_realtime.py first.")

    df = pd.read_csv(IN_CSV)

    # Make sure required cols exist
    missing = [c for c in ["feed_timestamp", "route_id", "stop_id"] if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}\nCols: {list(df.columns)}")

    # IMPORTANT: use feed_timestamp (epoch seconds) for gap computation
    df["feed_timestamp"] = pd.to_numeric(df["feed_timestamp"], errors="coerce")

    # Drop rows missing keys/time
    df = df.dropna(subset=["feed_timestamp", "route_id", "stop_id"]).copy()

    # Sort so diff() makes sense
    df = df.sort_values(["route_id", "stop_id", "feed_timestamp"])

    # gap_seconds = time between consecutive feed updates for same route_id+stop_id
    df["gap_seconds"] = (
        df.groupby(["route_id", "stop_id"])["feed_timestamp"].diff()
    )

    # Keep only rows where we can compute a gap
    out = df.dropna(subset=["gap_seconds"]).copy()

    # Save a compact output (add more cols if you want)
    keep_cols = []
    for c in (PRIMARY_COLS + ["gap_seconds"]):
        if c in out.columns:
            keep_cols.append(c)

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    out[keep_cols].to_csv(OUT_CSV, index=False)

    print(f"[OK] Wrote {len(out)} rows -> {OUT_CSV}")
    print(f"Non-null gap_seconds: {int(out['gap_seconds'].notna().sum())}")
    print(out[["route_id", "stop_id", "feed_timestamp", "gap_seconds"]].head(10))


if __name__ == "__main__":
    main()
