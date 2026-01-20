import os
import pandas as pd

IN_CSV = "data/raw/trip_updates.csv"
OUT_CSV = "data/processed/realtime_with_target.csv"

def main():
    if not os.path.exists(IN_CSV):
        raise FileNotFoundError(f"Missing {IN_CSV}")

    df = pd.read_csv(IN_CSV)

    # Count number of updates per route_id + stop_id within the feed
    counts = (
        df.groupby(["route_id", "stop_id"])
          .size()
          .reset_index(name="num_updates_at_stop")
    )

    # Join back to original rows (each row gets the target)
    out = df.merge(
        counts,
        on=["route_id", "stop_id"],
        how="left"
    )

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    print(f"[OK] Wrote {len(out)} rows -> {OUT_CSV}")
    print("Target summary:")
    print(out["num_updates_at_stop"].describe())
    print(out[["route_id", "stop_id", "num_updates_at_stop"]].head(10))

if __name__ == "__main__":
    main()

