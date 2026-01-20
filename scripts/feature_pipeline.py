import os
import time
import numpy as np
import pandas as pd
import hopsworks

FEATURES_CSV = "data/processed/realtime_with_target.csv"


FG_NAME = "realtime_features_target_fg"
FG_VERSION = 1

FG_DESCRIPTION = "GTFS-Realtime features joined with GTFS stops/routes (DelayLens)."

PRIMARY_KEYS = ["feed_timestamp", "trip_id", "stop_id"]
EVENT_TIME_COL = "feed_timestamp"

MAX_RETRIES = 3
SLEEP_SEC = 8


def clean_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix Avro union ["null","string"] issues by ensuring:
    - no np.nan in string columns
    - no literal "nan"/"NaN" strings
    - empty strings -> None
    """
    obj_cols = df.select_dtypes(include=["object"]).columns.tolist()

    for c in obj_cols:
        df[c] = df[c].replace({np.nan: None, "nan": None, "NaN": None, "": None})
        df[c] = df[c].astype(object)

    return df


def main():
    api_key = os.environ.get("HOPSWORKS_API_KEY")
    if not api_key:
        raise RuntimeError("HOPSWORKS_API_KEY is not set (export it in the same terminal before running).")

    if not os.path.exists(FEATURES_CSV):
        raise FileNotFoundError(
            f"Missing {FEATURES_CSV}. Run your pipeline first:\n"
            f"  python scripts/fetch_realtime.py\n"
            f"  python scripts/join_realtime_with_stops.py\n"
            f"  python scripts/join_with_routes.py"
        )

    # 1) Read CSV (treat 'nan'/'NaN'/'' as missing)
    df = pd.read_csv(
        FEATURES_CSV,
        keep_default_na=True,
        na_values=["nan", "NaN", ""],
    )

    # 2) Validate required columns
    missing = [c for c in (PRIMARY_KEYS + [EVENT_TIME_COL]) if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}\nColumns: {list(df.columns)}")

    # 3) Drop rows missing PKs
    df = df.dropna(subset=PRIMARY_KEYS).copy()

    # 4) Types: do NOT cast to str before cleaning
    df["feed_timestamp"] = pd.to_numeric(df["feed_timestamp"], errors="raise").astype("int64")

    # Clean ALL object columns (fixes stop_name, route_short_name, etc.)
    df = clean_string_columns(df)

    # Now force PKs to be strings (after cleaning)
    df["trip_id"] = df["trip_id"].astype(str)
    df["stop_id"] = df["stop_id"].astype(str)

    # delay_seconds numeric
    if "delay_seconds" in df.columns:
        df["delay_seconds"] = pd.to_numeric(df["delay_seconds"], errors="coerce")

    print(f"Loaded features: {df.shape[0]} rows, {df.shape[1]} cols")
    print(df.head(5))

    # 5) Hopsworks
    project = hopsworks.login(api_key_value=api_key)
    fs = project.get_feature_store()

    fg = fs.get_or_create_feature_group(
        name=FG_NAME,
        version=FG_VERSION,
        primary_key=PRIMARY_KEYS,
        event_time=EVENT_TIME_COL,
        description=FG_DESCRIPTION,
        online_enabled=False,
    )

    # 6) Insert with retry (Kafka/network can be flaky)
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # IMPORTANT: don't block waiting for the Hopsworks job to finish
            fg.insert(df, write_options={"wait_for_job": False})

            print(f"[OK] Insert request sent to Feature Group: {FG_NAME}_v{FG_VERSION}")
            print("[INFO] Materialization runs in Hopsworks asynchronously (we are NOT waiting here).")
            return

        except Exception as e:
            last_err = e
            print(f"[WARN] Insert attempt {attempt}/{MAX_RETRIES} failed: {type(e).__name__}: {e}")

            if attempt < MAX_RETRIES:
                time.sleep(SLEEP_SEC)

    raise RuntimeError(f"[ERROR] Failed to insert after retries. Last error: {last_err}")


if __name__ == "__main__":
    main()
